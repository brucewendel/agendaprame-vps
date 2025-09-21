import cx_Oracle
from utils.db_conection import db_manager
from services import senderzap_service # Importa o novo serviço
from datetime import datetime

def create_booking(data, user_id):
    """
    Agenda uma nova sala de reunião, verificando a disponibilidade.

    Args:
        data (dict): Dicionário com dados do agendamento (sala_id, inicio, fim, titulo, descricao).
        user_id (str): ID do usuário que está agendando, obtido do token JWT.

    Returns:
        tuple: (detalhes_do_agendamento, mensagem_de_erro)
    """
    conn = db_manager.connect()
    if not conn:
        return None, "Erro de conexão com o banco de dados."

    try:
        cursor = db_manager.connection.cursor()
        
        sala_id = data.get('sala_id')
        inicio = data.get('inicio')
        fim = data.get('fim')
        titulo = data.get('titulo')
        sala_nome = data.get('sala_nome', f"ID {sala_id}") # Pega o nome da sala do payload
        descricao = data.get('descricao')

        print(f"DEBUG: create_booking - sala_id: {sala_id} (type: {type(sala_id)})")
        print(f"DEBUG: create_booking - user_id: {user_id} (type: {type(user_id)})")
        print(f"DEBUG: create_booking - inicio: {inicio} (type: {type(inicio)})")
        print(f"DEBUG: create_booking - fim: {fim} (type: {type(fim)})")
        print(f"DEBUG: create_booking - titulo: {titulo} (type: {type(titulo)})")
        print(f"DEBUG: create_booking - descricao: {descricao} (type: {type(descricao)})")

        sql_check_conflict = """
            SELECT COUNT(*)
            FROM MX2_AGENDAMENTOS_SALA
            WHERE ID_SALA = :sala_id
            AND (
                (DATA_INICIO < TO_TIMESTAMP(:fim, 'YYYY-MM-DD"T"HH24:MI:SS')) AND
                (DATA_FIM > TO_TIMESTAMP(:inicio, 'YYYY-MM-DD"T"HH24:MI:SS'))
            )
        """
        cursor.execute(sql_check_conflict, sala_id=sala_id, inicio=inicio, fim=fim)
        conflict_count, = cursor.fetchone()

        print(f"DEBUG: Conflict Count: {conflict_count}")

        if conflict_count > 0:
            db_manager.connection.rollback()
            return None, "Conflito de horário! A sala já está agendada neste período."

        sql_insert_booking = """
            INSERT INTO MX2_AGENDAMENTOS_SALA (
                ID_SALA, ID_USUARIO, DATA_INICIO, DATA_FIM, TITULO, DESCRICAO
            ) VALUES (
                :sala_id, :user_id, TO_TIMESTAMP(:inicio, 'YYYY-MM-DD"T"HH24:MI:SS'),
                TO_TIMESTAMP(:fim, 'YYYY-MM-DD"T"HH24:MI:SS'), :titulo, :descricao
            )
            RETURNING ID_AGENDAMENTO INTO :id_agendamento
        """
        # Variável para capturar o ID que será retornado
        id_agendamento = cursor.var(cx_Oracle.NUMBER)
        
        cursor.execute(sql_insert_booking, 
                       sala_id=sala_id, 
                       user_id=user_id,
                       inicio=inicio,
                       fim=fim,
                       titulo=titulo,
                       descricao=descricao,
                       id_agendamento=id_agendamento)
        
        db_manager.connection.commit()

        # --- Início da Lógica de Notificação ---
        try:
            # Formata a mensagem para o WhatsApp
            dt_inicio_obj = datetime.strptime(inicio, '%Y-%m-%dT%H:%M:%S')
            dt_fim_obj = datetime.strptime(fim, '%Y-%m-%dT%H:%M:%S')
            
            dt_inicio_fmt = dt_inicio_obj.strftime('%d/%m/%Y às %H:%M')
            dt_fim_fmt = dt_fim_obj.strftime('%H:%M')

            mensagem = (
                f"📢 *Novo Agendamento de Sala*\n\n"
                f"A sala *{sala_nome}* foi agendada com os seguintes detalhes:\n\n"
                f"▪️ *Título:* {titulo}\n"
                f"▪️ *Início:* {dt_inicio_fmt}\n"
                f"▪️ *Fim:* {dt_fim_fmt}\n\n"
                f"```{descricao}```"
            )

            senderzap_service.send_whatsapp_message(senderzap_service.RECEPTION_PHONE, mensagem)

            if 'suporte de ti' in descricao.lower() or 'projetor' in descricao.lower():
                senderzap_service.send_whatsapp_message(senderzap_service.IT_PHONE, mensagem)
        except Exception as e:
            print(f"AVISO: O agendamento foi criado, mas a notificação por WhatsApp falhou: {e}")
        # --- Fim da Lógica de Notificação ---

        return {
            "id_agendamento": id_agendamento.getvalue()[0],
            "sala_id": sala_id,
            "data_inicio": inicio,
            "data_fim": fim,
            "titulo": titulo
        }, None

    except cx_Oracle.DatabaseError as e:
        db_manager.connection.rollback()
        error, = e.args
        return None, f"Erro no banco de dados: {error.message}"
    
    finally:
        db_manager.connection.close()


def get_bookings(start_date=None, end_date=None):
    """
    Retorna a lista de agendamentos com base em um período de data.
    """
    conn = db_manager.connect()
    if not conn:
        return [], "Erro de conexão com o banco de dados."

    try:
        cursor = db_manager.connection.cursor()
        
        sql_query = """
            SELECT
                ID_AGENDAMENTO, ID_SALA, ID_USUARIO, 
                TO_CHAR(DATA_INICIO, 'YYYY-MM-DD"T"HH24:MI:SS') AS DATA_INICIO, 
                TO_CHAR(DATA_FIM, 'YYYY-MM-DD"T"HH24:MI:SS') AS DATA_FIM, 
                TITULO
            FROM MX2_AGENDAMENTOS_SALA
            WHERE (:start_date IS NULL OR DATA_FIM > TO_TIMESTAMP(:start_date, 'YYYY-MM-DD"T"HH24:MI:SS'))
            AND (:end_date IS NULL OR DATA_INICIO < TO_TIMESTAMP(:end_date, 'YYYY-MM-DD"T"HH24:MI:SS'))
            ORDER BY DATA_INICIO ASC
        """
        
        cursor.execute(sql_query, start_date=start_date, end_date=end_date)
        bookings = cursor.fetchall()

        column_names = [desc[0] for desc in cursor.description]
        bookings_list = [dict(zip(column_names, booking)) for booking in bookings]

        return bookings_list, None

    except cx_Oracle.DatabaseError as e:
        error, = e.args
        return [], f"Erro ao buscar agendamentos: {error.message}"
    
    finally:
        db_manager.connection.close()


def update_booking(booking_id, data, user_id, user_profile):
    """
    Atualiza um agendamento existente, com validação de permissão e conflito.

    Args:
        booking_id (int): ID do agendamento a ser atualizado.
        data (dict): Dicionário com dados do agendamento (sala_id, inicio, fim, titulo, descricao).
        user_id (str): ID do usuário que está fazendo a requisição.
    """
    conn = db_manager.connect()
    if not conn:
        return None, "Erro de conexão com o banco de dados."

    try:
        cursor = db_manager.connection.cursor()
        
        sql_check_permission = """
            SELECT ID_USUARIO FROM MX2_AGENDAMENTOS_SALA WHERE ID_AGENDAMENTO = :booking_id
        """
        cursor.execute(sql_check_permission, booking_id=booking_id)
        booking_owner = cursor.fetchone()
        
        if not booking_owner:
            return None, "Agendamento não encontrado."
        
        if user_profile != 'Administrador' and booking_owner[0] != user_id:
            return None, "Você não tem permissão para editar este agendamento."

        sala_id = data.get('sala_id')
        inicio = data.get('inicio')
        fim = data.get('fim')
        
        sql_check_conflict = """
            SELECT COUNT(*)
            FROM MX2_AGENDAMENTOS_SALA
            WHERE ID_SALA = :sala_id
            AND ID_AGENDAMENTO != :booking_id
            AND (
                (DATA_INICIO < TO_TIMESTAMP(:fim, 'YYYY-MM-DD"T"HH24:MI:SS')) AND
                (DATA_FIM > TO_TIMESTAMP(:inicio, 'YYYY-MM-DD"T"HH24:MI:SS'))
            )
        """
        cursor.execute(sql_check_conflict, 
                       booking_id=booking_id,
                       sala_id=sala_id,
                       inicio=inicio,
                       fim=fim)
        conflict_count, = cursor.fetchone()

        if conflict_count > 0:
            db_manager.connection.rollback()
            return None, "Conflito de horário! A sala já está agendada neste novo período."

        sql_update_booking = """
            UPDATE MX2_AGENDAMENTOS_SALA
            SET
                ID_SALA = :sala_id,
                DATA_INICIO = TO_TIMESTAMP(:inicio, 'YYYY-MM-DD"T"HH24:MI:SS'),
                DATA_FIM = TO_TIMESTAMP(:fim, 'YYYY-MM-DD"T"HH24:MI:SS'),
                TITULO = :titulo,
                DESCRICAO = :descricao
            WHERE ID_AGENDAMENTO = :booking_id
        """
        cursor.execute(sql_update_booking,
                       booking_id=booking_id,
                       sala_id=sala_id,
                       inicio=inicio,
                       fim=fim,
                       titulo=data.get('titulo'),
                       descricao=data.get('descricao'))

        db_manager.connection.commit()
        
        return {
            "id_agendamento": booking_id,
            "sala_id": sala_id,
            "data_inicio": inicio,
            "data_fim": fim,
            "titulo": data.get('titulo')
        }, None

    except cx_Oracle.DatabaseError as e:
        db_manager.connection.rollback()
        error, = e.args
        return None, f"Erro no banco de dados: {error.message}"
    
    finally:
        db_manager.connection.close()


def delete_booking(booking_id, user_id, user_profile):
    """
    Exclui um agendamento, com validação de permissão.

    Args:
        booking_id (int): ID do agendamento a ser excluído.
        user_id (str): ID do usuário que está fazendo a requisição.
    """
    conn = db_manager.connect()
    if not conn:
        return False, "Erro de conexão com o banco de dados."

    try:
        cursor = db_manager.connection.cursor()
        
        sql_check_permission = """
            SELECT ID_USUARIO FROM MX2_AGENDAMENTOS_SALA WHERE ID_AGENDAMENTO = :booking_id
        """
        cursor.execute(sql_check_permission, booking_id=booking_id)
        booking_owner = cursor.fetchone()
        
        if not booking_owner:
            return False, "Agendamento não encontrado."
        
        if user_profile != 'Administrador' and booking_owner[0] != user_id:
            return False, "Você não tem permissão para cancelar este agendamento."
        
        sql_delete_booking = """
            DELETE FROM MX2_AGENDAMENTOS_SALA WHERE ID_AGENDAMENTO = :booking_id
        """
        cursor.execute(sql_delete_booking, booking_id=booking_id)
        db_manager.connection.commit()
        
        return True, None

    except cx_Oracle.DatabaseError as e:
        db_manager.connection.rollback()
        error, = e.args
        return False, f"Erro no banco de dados: {error.message}"
    
    finally:
        db_manager.connection.close()


def get_agendamento(id_agendamento):
    """
    Busca um agendamento pelo ID.

    Args:
        id_agendamento (int): ID do agendamento a ser buscado.

    Returns:
        dict: Detalhes do agendamento, se encontrado.
        str: Mensagem de erro, se houver.
    """
    conn = db_manager.connect()
    if not conn:
        return None, "Erro de conexão com o banco de dados."

    try:
        cursor = db_manager.connection.cursor()
        
        sql_query = """
            SELECT
                ID_AGENDAMENTO, ID_SALA, ID_USUARIO, 
                TO_CHAR(DATA_INICIO, 'YYYY-MM-DD"T"HH24:MI:SS') AS DATA_INICIO, 
                TO_CHAR(DATA_FIM, 'YYYY-MM-DD"T"HH24:MI:SS') AS DATA_FIM, 
                TITULO, DESCRICAO
            FROM MX2_AGENDAMENTOS_SALA
            WHERE ID_AGENDAMENTO = :id_agendamento
        """
        
        cursor.execute(sql_query, id_agendamento=id_agendamento)
        agendamento = cursor.fetchone()

        if not agendamento:
            return None, "Agendamento não encontrado."

        column_names = [desc[0] for desc in cursor.description]
        # Converte o resultado para um dicionário
        agendamento_dict = dict(zip(column_names, agendamento))

        # O objeto datetime já foi convertido para string pela query, então podemos retornar diretamente
        agendamento_details = agendamento_dict

        return agendamento_details, None

    except cx_Oracle.DatabaseError as e:
        error, = e.args
        return None, f"Erro ao buscar agendamento: {error.message}"
    
    finally:
        db_manager.connection.close()