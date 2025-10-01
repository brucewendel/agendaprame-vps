import cx_Oracle
from utils.db_conection import db_manager
from app.models import Room

class RoomService:
    def get_all_rooms(self):
        conn = db_manager.connect()
        if not conn:
            return None, "Erro de conexão com o banco de dados."
        try:
            cursor = db_manager.connection.cursor()
            sql = "SELECT ID_SALA, NOME_SALA, ATIVA FROM MX2_SALAS ORDER BY ID_SALA"
            cursor.execute(sql)
            rows = cursor.fetchall()
            rooms = []
            for row in rows:
                rooms.append(Room(id=row[0], name=row[1], active=bool(row[2])))
            return rooms, None
        except Exception as e:
            print(f"Erro ao buscar salas: {e}")
            return [], f"Erro ao buscar salas: {e}"  # Retorna lista vazia em vez de None
        finally:
            if db_manager.connection:
                db_manager.connection.close()

    def get_room_by_id(self, room_id):
        conn = db_manager.connect()
        if not conn:
            return None, "Erro de conexão com o banco de dados."
        try:
            cursor = db_manager.connection.cursor()
            sql = "SELECT ID_SALA, NOME_SALA, ATIVA FROM MX2_SALAS WHERE ID_SALA = :room_id"
            cursor.execute(sql, room_id=room_id)
            row = cursor.fetchone()
            if row:
                room = Room(id=row[0], name=row[1], active=bool(row[2]))
                return room, None
            return None, "Sala não encontrada."
        except Exception as e:
            print(f"Erro ao buscar sala por ID: {e}")
            return None, f"Erro ao buscar sala por ID: {e}"
        finally:
            if db_manager.connection:
                db_manager.connection.close()

    def create_room(self, name):
        conn = db_manager.connect()
        if not conn:
            return None, "Erro de conexão com o banco de dados."
        try:
            cursor = db_manager.connection.cursor()
            
            # Não precisamos mais gerar o ID manualmente, pois é uma coluna de identidade
            sql = "INSERT INTO MX2_SALAS (NOME_SALA, ATIVA) VALUES (:name, 1) RETURNING ID_SALA INTO :new_id"
            
            # Variável para receber o ID gerado automaticamente
            new_id_var = cursor.var(int)
            cursor.execute(sql, name=name, new_id=new_id_var)
            
            # Obtém o ID gerado
            new_id = new_id_var.getvalue()[0]
            
            db_manager.connection.commit()
            return Room(id=new_id, name=name, active=True), None
        except Exception as e:
            db_manager.connection.rollback()
            print(f"Erro ao criar sala: {e}")
            return None, f"Erro ao criar sala: {e}"
        finally:
            if db_manager.connection:
                db_manager.connection.close()

    def update_room(self, room_id, name, active):
        conn = db_manager.connect()
        if not conn:
            return None, "Erro de conexão com o banco de dados."
        try:
            cursor = db_manager.connection.cursor()
            sql = "UPDATE MX2_SALAS SET NOME_SALA = :name, ATIVA = :active WHERE ID_SALA = :room_id"
            
            print(f"SQL: {sql}, params: name={name}, active={int(active)}, room_id={room_id}")

            cursor.execute(sql, name=name, active=int(active), room_id=room_id)
            db_manager.connection.commit()

            if cursor.rowcount == 0:
                return None, "Sala não encontrada."
            
            return Room(id=room_id, name=name, active=active), None

        except cx_Oracle.DatabaseError as e:
            db_manager.connection.rollback()
            error_obj, = e.args
            print(f"Erro de DB ao atualizar: {error_obj.code} - {error_obj.message}")
            return None, f"Erro de DB: {error_obj.message}"

        except Exception as e:
            db_manager.connection.rollback()
            print(f"Erro inesperado ao atualizar: {e}")
            return None, f"Erro inesperado: {e}"

        finally:
            if db_manager.connection:
                db_manager.connection.close()

    def delete_room(self, room_id):
        conn = db_manager.connect()
        if not conn:
            return None, "Erro de conexão com o banco de dados."
        try:
            cursor = db_manager.connection.cursor()
            sql = "DELETE FROM MX2_SALAS WHERE ID_SALA = :room_id"
            cursor.execute(sql, room_id=room_id)
            db_manager.connection.commit()
            if cursor.rowcount == 0:
                return False, "Sala não encontrada."
            return True, None
        except Exception as e:
            db_manager.connection.rollback()
            print(f"Erro ao deletar sala: {e}")
            return False, f"Erro ao deletar sala: {e}"
        finally:
            if db_manager.connection:
                db_manager.connection.close()

room_service = RoomService()
