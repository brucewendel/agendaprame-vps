import logging
import os
import re
import threading

import cx_Oracle
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class bancoOracle:
    def __init__(self, username, password, hostname, port, service_name):
        self.username = username
        self.password = password
        self.hostname = hostname
        self.port = port
        self.service_name = service_name
        self.connection = None
        self.pool = None
        self._pool_lock = threading.Lock()
        self._password_hash_column_exists_cache = None
        self._metadata_lock = threading.Lock()

    def _ensure_pool(self):
        if self.pool is not None:
            return

        with self._pool_lock:
            if self.pool is not None:
                return

            dsn = cx_Oracle.makedsn(self.hostname, int(self.port), service_name=self.service_name)
            min_pool = int(os.environ.get('DB_POOL_MIN', '2'))
            max_pool = int(os.environ.get('DB_POOL_MAX', '20'))
            increment_pool = int(os.environ.get('DB_POOL_INCREMENT', '2'))

            self.pool = cx_Oracle.SessionPool(
                user=self.username,
                password=self.password,
                dsn=dsn,
                min=min_pool,
                max=max_pool,
                increment=increment_pool,
                threaded=True,
                encoding='UTF-8',
            )

    def connect(self):
        try:
            self._ensure_pool()
            self.connection = self.pool.acquire()
            return self.connection
        except cx_Oracle.DatabaseError:
            logger.exception('Erro ao conectar ao Oracle')
            return None

    def _get_password_hash_column_name(self) -> str:
        column_name = os.environ.get('PASSWORD_HASH_COLUMN', 'SENHA_HASH')
        if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', column_name or ''):
            logger.warning('Invalid PASSWORD_HASH_COLUMN, falling back to SENHA_HASH.')
            return 'SENHA_HASH'
        return column_name.upper()

    def _password_hash_column_exists(self, conn) -> bool:
        if self._password_hash_column_exists_cache is not None:
            return self._password_hash_column_exists_cache

        with self._metadata_lock:
            if self._password_hash_column_exists_cache is not None:
                return self._password_hash_column_exists_cache

            cursor = conn.cursor()
            try:
                cursor.execute(
                    """
                    SELECT 1
                    FROM USER_TAB_COLUMNS
                    WHERE TABLE_NAME = 'PCEMPR'
                      AND COLUMN_NAME = :column_name
                    FETCH FIRST 1 ROWS ONLY
                    """,
                    column_name=self._get_password_hash_column_name(),
                )
                self._password_hash_column_exists_cache = cursor.fetchone() is not None
            except cx_Oracle.DatabaseError:
                logger.exception('Failed checking password hash column existence.')
                self._password_hash_column_exists_cache = False
            finally:
                cursor.close()

            return self._password_hash_column_exists_cache

    def _build_user_lookup_query(self, include_hash_column: bool) -> str:
        hash_select = (
            f't.{self._get_password_hash_column_name()} AS senha_hash,'
            if include_hash_column
            else "CAST(NULL AS VARCHAR2(255)) AS senha_hash,"
        )
        return f"""
            SELECT
                t.matricula,
                t.nome,
                t.usuariobd,
                decrypt(t.senhabd, t.usuariobd) AS senha_descriptografada,
                {hash_select}
                t.codsetor,
                t.dt_exclusao,
                t.situacao,
                t.dtdemissao
            FROM pcempr t
            WHERE t.usuariobd = :login
        """

    def get_user_data_from_db(self, login):
        """Fetch user data with legacy password and optional hash column."""
        conn = self.connect()
        if not conn:
            return None, 'Erro de conexao com o banco de dados.'

        try:
            include_hash_column = self._password_hash_column_exists(conn)
            cursor = conn.cursor()
            sql_query = self._build_user_lookup_query(include_hash_column)
            cursor.execute(sql_query, login=login)
            row = cursor.fetchone()
            cursor.close()

            if not row:
                return None, 'Usuario nao encontrado.'

            return {
                'matricula': row[0],
                'nome': row[1],
                'usuariobd': row[2],
                'senha_descriptografada': row[3],
                'senha_hash': row[4],
                'codsetor': row[5],
                'dt_exclusao': row[6],
                'situacao': row[7],
                'dtdemissao': row[8],
                'has_password_hash_column': include_hash_column,
            }, None

        except cx_Oracle.DatabaseError:
            logger.exception('Erro ao buscar dados do usuario no Oracle')
            return None, 'Erro ao buscar dados do usuario.'
        finally:
            if conn:
                conn.close()

    def update_user_password_hash(self, login, password_hash: str):
        """Update bcrypt hash in configured password hash column."""
        conn = self.connect()
        if not conn:
            return False, 'Erro de conexao com o banco de dados.'

        try:
            if not self._password_hash_column_exists(conn):
                return False, 'Coluna de hash nao encontrada.'

            cursor = conn.cursor()
            sql_query = (
                f'UPDATE pcempr SET {self._get_password_hash_column_name()} = :password_hash '
                'WHERE usuariobd = :login'
            )
            cursor.execute(sql_query, password_hash=password_hash, login=login)
            conn.commit()
            updated = cursor.rowcount > 0
            cursor.close()
            return updated, None if updated else 'Usuario nao encontrado para migracao.'
        except cx_Oracle.DatabaseError:
            conn.rollback()
            logger.exception('Erro ao atualizar hash de senha.')
            return False, 'Erro ao atualizar hash de senha.'
        finally:
            if conn:
                conn.close()

    # Backward-compatible methods kept for legacy imports/tests.
    def create_booking(self, data, user_id):
        conn = self.connect()
        if not conn:
            return None, 'Erro de conexao com o banco de dados.'

        try:
            cursor = conn.cursor()

            sala_id = data.get('sala_id')
            inicio = data.get('inicio')
            fim = data.get('fim')
            titulo = data.get('titulo')
            descricao = data.get('descricao')

            sql_check_conflict = """
                SELECT 1
                FROM MX2_AGENDAMENTOS_SALA
                WHERE ID_SALA = :sala_id
                  AND DATA_INICIO < TO_TIMESTAMP(:fim, 'YYYY-MM-DD"T"HH24:MI:SS')
                  AND DATA_FIM > TO_TIMESTAMP(:inicio, 'YYYY-MM-DD"T"HH24:MI:SS')
                  FETCH FIRST 1 ROWS ONLY
            """
            cursor.execute(sql_check_conflict, sala_id=sala_id, inicio=inicio, fim=fim)
            conflict = cursor.fetchone()

            if conflict:
                conn.rollback()
                return None, 'Conflito de horario para a sala selecionada.'

            sql_insert_booking = """
                INSERT INTO MX2_AGENDAMENTOS_SALA (
                    ID_SALA, ID_USUARIO, DATA_INICIO, DATA_FIM, TITULO, DESCRICAO
                ) VALUES (
                    :sala_id, :user_id, TO_TIMESTAMP(:inicio, 'YYYY-MM-DD"T"HH24:MI:SS'),
                    TO_TIMESTAMP(:fim, 'YYYY-MM-DD"T"HH24:MI:SS'), :titulo, :descricao
                )
            """
            cursor.execute(
                sql_insert_booking,
                sala_id=sala_id,
                user_id=user_id,
                inicio=inicio,
                fim=fim,
                titulo=titulo,
                descricao=descricao,
            )
            conn.commit()

            return {
                'sala_id': sala_id,
                'data_inicio': inicio,
                'data_fim': fim,
                'titulo': titulo,
            }, None

        except cx_Oracle.DatabaseError:
            conn.rollback()
            logger.exception('Erro ao criar agendamento (legacy path)')
            return None, 'Erro interno no banco de dados.'
        finally:
            if conn:
                conn.close()

    def get_agendamento(self, id_agendamento):
        conn = self.connect()
        if not conn:
            return None, 'Erro de conexao com o banco de dados.'
        try:
            cursor = conn.cursor()
            sql = """
                SELECT ID_AGENDAMENTO, ID_SALA, ID_USUARIO, DATA_INICIO, DATA_FIM, TITULO
                FROM MX2_AGENDAMENTOS_SALA
                WHERE ID_AGENDAMENTO = :id_agendamento
            """
            cursor.execute(sql, id_agendamento=id_agendamento)
            result = cursor.fetchone()
            if result:
                return {
                    'ID_AGENDAMENTO': result[0],
                    'ID_SALA': result[1],
                    'ID_USUARIO': result[2],
                    'DATA_INICIO': result[3],
                    'DATA_FIM': result[4],
                    'TITULO': result[5],
                }, None
            return None, 'Agendamento nao encontrado.'
        except cx_Oracle.DatabaseError:
            logger.exception('Erro ao buscar agendamento (legacy path)')
            return None, 'Erro interno no banco de dados.'
        finally:
            if conn:
                conn.close()


# Initialize singleton manager
db_manager = bancoOracle(
    username=os.environ.get('DB_USER'),
    password=os.environ.get('DB_PASSWORD'),
    hostname=os.environ.get('HOST'),
    port=os.environ.get('PORT'),
    service_name=os.environ.get('SERVICE_NAME'),
)
