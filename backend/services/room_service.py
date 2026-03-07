import logging

import cx_Oracle

from app.models import Room
from utils.db_conection import db_manager

logger = logging.getLogger(__name__)


class RoomService:
    def get_all_rooms(self):
        conn = db_manager.connect()
        if not conn:
            return None, 'Erro de conexao com o banco de dados.'
        try:
            cursor = conn.cursor()
            sql = 'SELECT ID_SALA, NOME_SALA, ATIVA FROM MX2_SALAS ORDER BY ID_SALA'
            cursor.execute(sql)
            rows = cursor.fetchall()
            rooms = [Room(id=row[0], name=row[1], active=bool(row[2])) for row in rows]
            return rooms, None
        except cx_Oracle.DatabaseError:
            logger.exception('Erro de banco ao buscar salas')
            return [], 'Erro interno ao buscar salas.'
        finally:
            if conn:
                conn.close()

    def get_room_by_id(self, room_id):
        conn = db_manager.connect()
        if not conn:
            return None, 'Erro de conexao com o banco de dados.'
        try:
            cursor = conn.cursor()
            sql = 'SELECT ID_SALA, NOME_SALA, ATIVA FROM MX2_SALAS WHERE ID_SALA = :room_id'
            cursor.execute(sql, room_id=room_id)
            row = cursor.fetchone()
            if row:
                return Room(id=row[0], name=row[1], active=bool(row[2])), None
            return None, 'Sala nao encontrada.'
        except cx_Oracle.DatabaseError:
            logger.exception('Erro de banco ao buscar sala por ID')
            return None, 'Erro interno ao buscar sala.'
        finally:
            if conn:
                conn.close()

    def create_room(self, name):
        conn = db_manager.connect()
        if not conn:
            return None, 'Erro de conexao com o banco de dados.'
        try:
            cursor = conn.cursor()
            sql = 'INSERT INTO MX2_SALAS (NOME_SALA, ATIVA) VALUES (:name, 1) RETURNING ID_SALA INTO :new_id'
            new_id_var = cursor.var(int)
            cursor.execute(sql, name=name, new_id=new_id_var)
            new_id = new_id_var.getvalue()[0]
            conn.commit()
            return Room(id=new_id, name=name, active=True), None
        except cx_Oracle.DatabaseError:
            conn.rollback()
            logger.exception('Erro de banco ao criar sala')
            return None, 'Erro interno ao criar sala.'
        finally:
            if conn:
                conn.close()

    def update_room(self, room_id, name, active):
        conn = db_manager.connect()
        if not conn:
            return None, 'Erro de conexao com o banco de dados.'
        try:
            cursor = conn.cursor()
            sql = 'UPDATE MX2_SALAS SET NOME_SALA = :name, ATIVA = :active WHERE ID_SALA = :room_id'
            cursor.execute(sql, name=name, active=int(active), room_id=room_id)
            conn.commit()

            if cursor.rowcount == 0:
                return None, 'Sala nao encontrada.'

            return Room(id=room_id, name=name, active=active), None
        except cx_Oracle.DatabaseError:
            conn.rollback()
            logger.exception('Erro de banco ao atualizar sala')
            return None, 'Erro interno ao atualizar sala.'
        finally:
            if conn:
                conn.close()

    def delete_room(self, room_id):
        conn = db_manager.connect()
        if not conn:
            return None, 'Erro de conexao com o banco de dados.'
        try:
            cursor = conn.cursor()
            sql = 'DELETE FROM MX2_SALAS WHERE ID_SALA = :room_id'
            cursor.execute(sql, room_id=room_id)
            conn.commit()
            if cursor.rowcount == 0:
                return False, 'Sala nao encontrada.'
            return True, None
        except cx_Oracle.DatabaseError:
            conn.rollback()
            logger.exception('Erro de banco ao deletar sala')
            return False, 'Erro interno ao deletar sala.'
        finally:
            if conn:
                conn.close()


room_service = RoomService()
