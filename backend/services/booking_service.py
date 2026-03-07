import logging
import threading
from datetime import datetime, timedelta

import cx_Oracle

from services import email_service, senderzap_service
from utils.db_conection import db_manager

logger = logging.getLogger(__name__)


def _normalize_datetime(value: str, field_name: str) -> tuple[datetime | None, str | None, str | None]:
    if not value:
        return None, None, f'Campo {field_name} e obrigatorio.'

    normalized = value
    if len(normalized.split(':')) == 2:
        normalized += ':00'
    if '.' in normalized:
        normalized = normalized.split('.')[0]

    try:
        dt = datetime.strptime(normalized, '%Y-%m-%dT%H:%M:%S')
        return dt, normalized, None
    except (ValueError, TypeError):
        return None, None, f'Formato de data invalido para {field_name}. Use YYYY-MM-DDTHH:MM:SS.'


def _has_conflict(cursor, sala_id, inicio_iso, fim_iso, exclude_booking_id=None):
    sql = """
        SELECT 1
        FROM MX2_AGENDAMENTOS_SALA
        WHERE ID_SALA = :sala_id
          AND DATA_INICIO < TO_TIMESTAMP(:fim, 'YYYY-MM-DD"T"HH24:MI:SS')
          AND DATA_FIM > TO_TIMESTAMP(:inicio, 'YYYY-MM-DD"T"HH24:MI:SS')
    """
    params = {'sala_id': sala_id, 'inicio': inicio_iso, 'fim': fim_iso}

    if exclude_booking_id is not None:
        sql += ' AND ID_AGENDAMENTO != :exclude_booking_id'
        params['exclude_booking_id'] = exclude_booking_id

    sql += ' FETCH FIRST 1 ROWS ONLY'
    cursor.execute(sql, params)
    return cursor.fetchone() is not None


def _get_user_contact(cursor, user_id):
    cursor.execute('SELECT email, nome FROM pcempr WHERE matricula = :user_id', user_id=user_id)
    return cursor.fetchone()


def _get_room_name(cursor, sala_id):
    cursor.execute('SELECT NOME_SALA FROM mx2_salas WHERE id_sala = :sala_id', sala_id=sala_id)
    row = cursor.fetchone()
    return row[0] if row else f'ID {sala_id}'


def create_booking(data, user_id):
    conn = db_manager.connect()
    if not conn:
        return None, 'Erro de conexao com o banco de dados.'

    try:
        cursor = conn.cursor()

        sala_id = data.get('sala_id')
        titulo = data.get('titulo')
        descricao = data.get('descricao')
        sala_nome = data.get('sala_nome', f'ID {sala_id}')

        inicio_dt, inicio_iso, err_inicio = _normalize_datetime(data.get('inicio'), 'inicio')
        if err_inicio:
            return None, err_inicio

        fim_dt, fim_iso, err_fim = _normalize_datetime(data.get('fim'), 'fim')
        if err_fim:
            return None, err_fim

        if inicio_dt < datetime.now() - timedelta(hours=24):
            return None, 'Nao e possivel agendar ou alterar para uma data passada ha mais de 24 horas.'
        if fim_dt <= inicio_dt:
            return None, 'A data de termino deve ser posterior a data de inicio.'

        if _has_conflict(cursor, sala_id, inicio_iso, fim_iso):
            conn.rollback()
            return None, 'Conflito de horario! A sala ja esta agendada neste periodo.'

        sql_insert = """
            INSERT INTO MX2_AGENDAMENTOS_SALA (
                ID_SALA, ID_USUARIO, DATA_INICIO, DATA_FIM, TITULO, DESCRICAO
            ) VALUES (
                :sala_id,
                :user_id,
                TO_TIMESTAMP(:inicio, 'YYYY-MM-DD"T"HH24:MI:SS'),
                TO_TIMESTAMP(:fim, 'YYYY-MM-DD"T"HH24:MI:SS'),
                :titulo,
                :descricao
            )
            RETURNING ID_AGENDAMENTO INTO :id_agendamento
        """

        id_agendamento = cursor.var(cx_Oracle.NUMBER)
        cursor.execute(
            sql_insert,
            sala_id=sala_id,
            user_id=user_id,
            inicio=inicio_iso,
            fim=fim_iso,
            titulo=titulo,
            descricao=descricao,
            id_agendamento=id_agendamento,
        )
        conn.commit()

        # Notifications are best-effort: booking must succeed even if notifications fail.
        try:
            dt_inicio_fmt = inicio_dt.strftime('%d/%m/%Y as %H:%M')
            dt_fim_fmt = fim_dt.strftime('%H:%M')
            descricao_txt = descricao or ''
            mensagem = (
                f'*Novo Agendamento de Sala*\n\n'
                f'Sala: {sala_nome}\n'
                f'Titulo: {titulo}\n'
                f'Inicio: {dt_inicio_fmt}\n'
                f'Fim: {dt_fim_fmt}\n\n'
                f'{descricao_txt}'
            )
            senderzap_service.send_whatsapp_message(senderzap_service.RECEPTION_PHONE, mensagem)
            if 'suporte de ti' in descricao_txt.lower() or 'projetor' in descricao_txt.lower():
                senderzap_service.send_whatsapp_message(senderzap_service.IT_PHONE, mensagem)
        except Exception:
            logger.warning('Falha no envio de notificacao WhatsApp apos criar agendamento.', exc_info=True)

        try:
            user_data = _get_user_contact(cursor, user_id)
            if user_data and user_data[0]:
                recipient_email, user_name = user_data
                booking_details = {
                    'summary': titulo,
                    'dtstart': inicio_dt,
                    'dtend': fim_dt,
                    'description': descricao,
                    'location': sala_nome,
                    'user_name': (user_name or '').strip(),
                }
                email_thread = threading.Thread(
                    target=email_service.send_booking_confirmation,
                    args=(recipient_email, booking_details),
                    daemon=True,
                )
                email_thread.start()
            else:
                logger.warning('Email do usuario %s nao encontrado para envio de convite.', user_id)
        except Exception:
            logger.warning('Falha no envio de notificacao por email apos criar agendamento.', exc_info=True)

        return {
            'id_agendamento': id_agendamento.getvalue()[0],
            'sala_id': sala_id,
            'data_inicio': inicio_iso,
            'data_fim': fim_iso,
            'titulo': titulo,
        }, None

    except cx_Oracle.DatabaseError:
        conn.rollback()
        logger.exception('Database error while creating booking')
        return None, 'Erro interno no banco de dados.'
    finally:
        conn.close()


def get_bookings(start_date=None, end_date=None):
    conn = db_manager.connect()
    if not conn:
        return [], 'Erro de conexao com o banco de dados.'

    try:
        cursor = conn.cursor()

        sql_query = """
            SELECT
                a.ID_AGENDAMENTO,
                a.ID_SALA,
                a.ID_USUARIO,
                TO_CHAR(a.DATA_INICIO, 'YYYY-MM-DD"T"HH24:MI:SS') AS DATA_INICIO,
                TO_CHAR(a.DATA_FIM, 'YYYY-MM-DD"T"HH24:MI:SS') AS DATA_FIM,
                a.TITULO,
                u.nome AS NOME_USUARIO
            FROM MX2_AGENDAMENTOS_SALA a
            LEFT JOIN pcempr u ON a.ID_USUARIO = u.matricula
        """

        where_clauses = []
        params = {}

        if start_date:
            where_clauses.append("a.DATA_FIM > TO_TIMESTAMP(:start_date, 'YYYY-MM-DD\"T\"HH24:MI:SS')")
            params['start_date'] = start_date

        if end_date:
            where_clauses.append("a.DATA_INICIO < TO_TIMESTAMP(:end_date, 'YYYY-MM-DD\"T\"HH24:MI:SS')")
            params['end_date'] = end_date

        if where_clauses:
            sql_query += ' WHERE ' + ' AND '.join(where_clauses)

        sql_query += ' ORDER BY a.DATA_INICIO ASC'
        cursor.execute(sql_query, params)
        bookings = cursor.fetchall()

        column_names = [desc[0] for desc in cursor.description]
        bookings_list = [dict(zip(column_names, booking)) for booking in bookings]
        return bookings_list, None

    except cx_Oracle.DatabaseError:
        logger.exception('Database error while fetching bookings')
        return [], 'Erro interno ao buscar agendamentos.'
    finally:
        conn.close()


def update_booking(booking_id, data, user_id, user_profile):
    conn = db_manager.connect()
    if not conn:
        return None, 'Erro de conexao com o banco de dados.'

    try:
        cursor = conn.cursor()

        cursor.execute(
            'SELECT ID_USUARIO FROM MX2_AGENDAMENTOS_SALA WHERE ID_AGENDAMENTO = :booking_id',
            booking_id=booking_id,
        )
        booking_owner = cursor.fetchone()
        if not booking_owner:
            return None, 'Agendamento nao encontrado.'

        if user_profile != 'Administrador' and str(booking_owner[0]) != str(user_id):
            return None, 'Voce nao tem permissao para editar este agendamento.'

        sala_id = data.get('sala_id')
        titulo = data.get('titulo')
        descricao = data.get('descricao')

        inicio_dt, inicio_iso, err_inicio = _normalize_datetime(data.get('inicio'), 'inicio')
        if err_inicio:
            return None, err_inicio

        fim_dt, fim_iso, err_fim = _normalize_datetime(data.get('fim'), 'fim')
        if err_fim:
            return None, err_fim

        if inicio_dt < datetime.now() - timedelta(hours=24):
            return None, 'Nao e possivel agendar ou alterar para uma data passada ha mais de 24 horas.'
        if fim_dt <= inicio_dt:
            return None, 'A data de termino deve ser posterior a data de inicio.'

        if _has_conflict(cursor, sala_id, inicio_iso, fim_iso, exclude_booking_id=booking_id):
            conn.rollback()
            return None, 'Conflito de horario! A sala ja esta agendada neste novo periodo.'

        params = {
            'booking_id': booking_id,
            'sala_id': sala_id,
            'inicio': inicio_iso,
            'fim': fim_iso,
            'titulo': titulo,
            'descricao': descricao,
        }

        set_clause = """
            ID_SALA = :sala_id,
            DATA_INICIO = TO_TIMESTAMP(:inicio, 'YYYY-MM-DD"T"HH24:MI:SS'),
            DATA_FIM = TO_TIMESTAMP(:fim, 'YYYY-MM-DD"T"HH24:MI:SS'),
            TITULO = :titulo,
            DESCRICAO = :descricao
        """

        if user_profile == 'Administrador' and 'id_usuario' in data:
            set_clause += ', ID_USUARIO = :id_usuario'
            params['id_usuario'] = data['id_usuario']

        sql_update = f'UPDATE MX2_AGENDAMENTOS_SALA SET {set_clause} WHERE ID_AGENDAMENTO = :booking_id'
        cursor.execute(sql_update, params)
        conn.commit()

        try:
            final_owner_id = params.get('id_usuario', booking_owner[0])
            user_data = _get_user_contact(cursor, final_owner_id)
            if user_data and user_data[0]:
                recipient_email, user_name = user_data
                sala_nome = _get_room_name(cursor, sala_id)
                booking_details = {
                    'summary': titulo,
                    'dtstart': inicio_dt,
                    'dtend': fim_dt,
                    'description': descricao,
                    'location': sala_nome,
                    'user_name': (user_name or '').strip(),
                }
                email_thread = threading.Thread(
                    target=email_service.send_booking_update_notification,
                    args=(recipient_email, booking_details),
                    daemon=True,
                )
                email_thread.start()
        except Exception:
            logger.warning('Falha no envio de notificacao por email apos atualizar agendamento.', exc_info=True)

        return {
            'id_agendamento': booking_id,
            'sala_id': sala_id,
            'data_inicio': inicio_iso,
            'data_fim': fim_iso,
            'titulo': titulo,
        }, None

    except cx_Oracle.DatabaseError:
        conn.rollback()
        logger.exception('Database error while updating booking')
        return None, 'Erro interno no banco de dados.'
    finally:
        conn.close()


def delete_booking(booking_id, user_id, user_profile):
    conn = db_manager.connect()
    if not conn:
        return False, 'Erro de conexao com o banco de dados.'

    try:
        cursor = conn.cursor()

        sql_get_details = """
            SELECT a.TITULO, a.DATA_INICIO, a.DATA_FIM, s.NOME_SALA AS NOME_SALA, u.email, u.nome
            FROM MX2_AGENDAMENTOS_SALA a
            LEFT JOIN pcempr u ON a.ID_USUARIO = u.matricula
            LEFT JOIN mx2_salas s ON a.ID_SALA = s.id_sala
            WHERE a.ID_AGENDAMENTO = :booking_id
        """
        cursor.execute(sql_get_details, booking_id=booking_id)
        notification_details = cursor.fetchone()

        cursor.execute(
            'SELECT ID_USUARIO FROM MX2_AGENDAMENTOS_SALA WHERE ID_AGENDAMENTO = :booking_id',
            booking_id=booking_id,
        )
        booking_owner = cursor.fetchone()

        if not booking_owner:
            return False, 'Agendamento nao encontrado.'

        if user_profile != 'Administrador' and str(booking_owner[0]) != str(user_id):
            return False, 'Voce nao tem permissao para cancelar este agendamento.'

        cursor.execute('DELETE FROM MX2_AGENDAMENTOS_SALA WHERE ID_AGENDAMENTO = :booking_id', booking_id=booking_id)
        conn.commit()

        try:
            if notification_details:
                summary, dtstart, dtend, location, recipient_email, user_name = notification_details
                booking_details = {
                    'summary': summary,
                    'dtstart': dtstart,
                    'dtend': dtend,
                    'location': location,
                    'user_name': user_name.strip() if user_name else '',
                }
                email_thread = threading.Thread(
                    target=email_service.send_booking_cancellation_notification,
                    args=(recipient_email, booking_details),
                    daemon=True,
                )
                email_thread.start()
        except Exception:
            logger.warning('Falha no envio de notificacao por email apos cancelar agendamento.', exc_info=True)

        return True, None

    except cx_Oracle.DatabaseError:
        conn.rollback()
        logger.exception('Database error while deleting booking')
        return False, 'Erro interno no banco de dados.'
    finally:
        conn.close()


def get_agendamento(id_agendamento):
    conn = db_manager.connect()
    if not conn:
        return None, 'Erro de conexao com o banco de dados.'

    try:
        cursor = conn.cursor()
        sql_query = """
            SELECT
                a.ID_AGENDAMENTO,
                a.ID_SALA,
                a.ID_USUARIO,
                TO_CHAR(a.DATA_INICIO, 'YYYY-MM-DD"T"HH24:MI:SS') AS DATA_INICIO,
                TO_CHAR(a.DATA_FIM, 'YYYY-MM-DD"T"HH24:MI:SS') AS DATA_FIM,
                a.TITULO,
                a.DESCRICAO,
                u.nome AS NOME_USUARIO
            FROM MX2_AGENDAMENTOS_SALA a
            LEFT JOIN pcempr u ON a.ID_USUARIO = u.matricula
            WHERE a.ID_AGENDAMENTO = :id_agendamento
        """
        cursor.execute(sql_query, id_agendamento=id_agendamento)
        agendamento = cursor.fetchone()

        if not agendamento:
            return None, 'Agendamento nao encontrado.'

        column_names = [desc[0] for desc in cursor.description]
        agendamento_dict = dict(zip(column_names, agendamento))
        return agendamento_dict, None

    except cx_Oracle.DatabaseError:
        logger.exception('Database error while fetching booking details')
        return None, 'Erro interno ao buscar agendamento.'
    finally:
        conn.close()
