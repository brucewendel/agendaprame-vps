import cx_Oracle
import os
from dotenv import load_dotenv

load_dotenv()

class bancoOracle:
    def __init__(self, username, password, hostname, port, service_name):
        self.username = username
        self.password = password
        self.hostname = hostname
        self.port = port
        self.service_name = service_name
        self.connection = None

    def connect(self):
        try:
            dsn = cx_Oracle.makedsn(self.hostname, self.port, service_name=self.service_name)
            self.connection = cx_Oracle.connect(user=self.username, password=self.password, dsn=dsn)
            return True
        except cx_Oracle.DatabaseError as e:
            print(f"Erro ao conectar ao Oracle: {e}")
            return False

    def get_user_data_from_db(self, login):
        """
        Busca dados do usuário e a senha descriptografada, usando a nova conexão.
        """
        if not self.connect():
            return None, "Erro de conexão com o banco de dados."
        
        try:
            cursor = self.connection.cursor()
            
            sql_query = """
                SELECT
                    t.matricula,
                    t.nome,
                    t.usuariobd,
                    decrypt(t.senhabd, t.usuariobd) as senha_descriptografada,
                    t.codsetor,
                    t.dt_exclusao,
                    t.situacao,
                    t.dtdemissao
                FROM pcempr t
                WHERE t.usuariobd = :login
            """
            
            cursor.execute(sql_query, login=login)
            user_data = cursor.fetchone()
            
            if user_data:
                return user_data, None
            else:
                return None, "Usuário não encontrado."

        except cx_Oracle.DatabaseError as e:
            print("Erro ao executar a query:", e)
            return None, "Erro ao buscar dados do usuário."
        finally:
            if self.connection:
                self.connection.close()

    def create_booking(self, data, user_id):
        """
        Agenda uma nova sala de reunião, verificando a disponibilidade.
        """
        if not self.connect():
            return None, "Erro de conexão com o banco de dados."

        try:
            cursor = self.connection.cursor()
            
            sala_id = data.get('sala_id')
            inicio = data.get('inicio')
            fim = data.get('fim')
            titulo = data.get('titulo')
            descricao = data.get('descricao')

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

            if conflict_count > 0:
                self.connection.rollback()
                return None, "Conflito de horário! A sala já está agendada neste período."

            sql_insert_booking = """
                INSERT INTO MX2_AGENDAMENTOS_SALA (
                    ID_SALA, ID_USUARIO, DATA_INICIO, DATA_FIM, TITULO, DESCRICAO
                ) VALUES (
                    :sala_id, :user_id, TO_TIMESTAMP(:inicio, 'YYYY-MM-DD"T"HH24:MI:SS'),
                    TO_TIMESTAMP(:fim, 'YYYY-MM-DD"T"HH24:MI:SS'), :titulo, :descricao
                )
            """
            cursor.execute(sql_insert_booking, 
                           sala_id=sala_id, 
                           user_id=user_id,
                           inicio=inicio,
                           fim=fim,
                           titulo=titulo,
                           descricao=descricao)
            
            self.connection.commit()

            return {
                "sala_id": sala_id,
                "data_inicio": inicio,
                "data_fim": fim,
                "titulo": titulo
            }, None

        except cx_Oracle.DatabaseError as e:
            self.connection.rollback()
            print(f"Erro no banco de dados: {e}")
            return None, f"Erro no banco de dados: {e}"
        finally:
            if self.connection:
                self.connection.close()

    def get_agendamento(self, id_agendamento):
        if not self.connect():
            return None, "Erro de conexão com o banco de dados."
        try:
            cursor = self.connection.cursor()
            sql = """
                SELECT ID_AGENDAMENTO, ID_SALA, ID_USUARIO, DATA_INICIO, DATA_FIM, TITULO
                FROM MX2_AGENDAMENTOS_SALA
                WHERE ID_AGENDAMENTO = :id_agendamento
            """
            cursor.execute(sql, id_agendamento=id_agendamento)
            result = cursor.fetchone()
            if result:
                agendamento = {
                    "ID_AGENDAMENTO": result[0],
                    "ID_SALA": result[1],
                    "ID_USUARIO": result[2],
                    "DATA_INICIO": result[3],
                    "DATA_FIM": result[4],
                    "TITULO": result[5]
                }
                return agendamento, None
            else:
                return None, "Agendamento não encontrado."
        except Exception as e:
            return None, str(e)
        finally:
            if self.connection:
                self.connection.close()


# Inicializa a classe e a deixa disponível para importação
db_manager = bancoOracle(
    username=os.environ.get('DB_USER'),
    password=os.environ.get('DB_PASSWORD'),
    hostname=os.environ.get('HOST'),
    port=os.environ.get('PORT'),
    service_name=os.environ.get('SERVICE_NAME')
)


# ...TESTANDO CONEXAO COM O BANCO...

# if __name__ == "__main__":
#     if db_manager.connect():
#         print("Conexão com Oracle estabelecida com sucesso!")
#         try:
#             cursor = db_manager.connection.cursor()
#             sql = """
#                 SELECT decrypt(senhabd, usuariobd)
#                 FROM pcempr
#                 WHERE matricula = '5063'
#             """
#             cursor.execute(sql)
#             resultado = cursor.fetchone()
#             if resultado:
#                 print("Resultado:", resultado)
#             else:
#                 print("Nenhum registro encontrado.")
#         except cx_Oracle.DatabaseError as e:
#             print("Erro ao executar o SELECT:", e)
#         finally:
#             db_manager.connection.close()
#     else:
#         print("Falha ao conectar ao Oracle.")