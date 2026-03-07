import hmac
import logging
import os
import uuid
from datetime import datetime, timedelta

import bcrypt
import cx_Oracle
import jwt

from utils.db_conection import db_manager

logger = logging.getLogger(__name__)


def _safe_str(value) -> str:
    return '' if value is None else str(value)


def _is_true_env(name: str, default: bool) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {'1', 'true', 'yes', 'on'}


def _is_bcrypt_hash(value: str | None) -> bool:
    if not value:
        return False
    return value.startswith('$2a$') or value.startswith('$2b$') or value.startswith('$2y$')


def _build_auth_payload(user_data):
    perfil = 'Administrador' if user_data['codsetor'] == 15 else 'Funcionario'
    secret_key = os.environ.get('SECRET_KEY')
    if not secret_key:
        logger.error('Missing SECRET_KEY in environment.')
        return None, 'Erro de autenticacao.'

    now = datetime.utcnow()
    token_lifetime_hours = int(os.environ.get('JWT_EXP_HOURS', '24'))
    payload = {
        'user_id': user_data['matricula'],
        'profile': perfil,
        'iat': now,
        'exp': now + timedelta(hours=token_lifetime_hours),
        'jti': str(uuid.uuid4()),
    }
    token = jwt.encode(payload, secret_key, algorithm='HS256')
    if isinstance(token, bytes):
        token = token.decode('utf-8')

    return {
        'token': token,
        'profile': perfil,
        'name': user_data['nome'],
    }, None


def _verify_legacy_password(user_data, senha_fornecida: str) -> bool:
    return hmac.compare_digest(
        _safe_str(user_data.get('senha_descriptografada')),
        _safe_str(senha_fornecida),
    )


def _migrate_password_hash_if_enabled(login: str, senha_fornecida: str, user_data) -> None:
    if not _is_true_env('PASSWORD_MIGRATE_ON_LOGIN', True):
        return
    if not user_data.get('has_password_hash_column'):
        return

    rounds = int(os.environ.get('PASSWORD_HASH_ROUNDS', '12'))
    password_hash = bcrypt.hashpw(
        _safe_str(senha_fornecida).encode('utf-8'),
        bcrypt.gensalt(rounds=rounds),
    ).decode('utf-8')

    updated, error = db_manager.update_user_password_hash(login, password_hash)
    if not updated:
        logger.warning('Password hash migration skipped for login=%s: %s', login, error)


def authenticate_user(login, senha_fornecida):
    """Authenticate user supporting bcrypt hash and legacy fallback."""
    user_data, error = db_manager.get_user_data_from_db(login)

    if error or not user_data:
        logger.warning('Authentication lookup failed for login=%s', login)
        return None, 'Credenciais invalidas.'

    if (
        user_data.get('situacao') != 'A'
        or user_data.get('dt_exclusao') is not None
        or user_data.get('dtdemissao') is not None
    ):
        return None, 'Credenciais invalidas.'

    provided_password = _safe_str(senha_fornecida)
    stored_hash = _safe_str(user_data.get('senha_hash'))
    hash_checked = False

    if _is_bcrypt_hash(stored_hash):
        hash_checked = True
        try:
            if not bcrypt.checkpw(provided_password.encode('utf-8'), stored_hash.encode('utf-8')):
                return None, 'Credenciais invalidas.'
        except ValueError:
            logger.warning('Invalid bcrypt hash format for login=%s', login)
            return None, 'Credenciais invalidas.'

    if not hash_checked:
        if not _is_true_env('ALLOW_LEGACY_PASSWORD', True):
            return None, 'Credenciais invalidas.'

        if not _verify_legacy_password(user_data, provided_password):
            return None, 'Credenciais invalidas.'

        try:
            _migrate_password_hash_if_enabled(login, provided_password, user_data)
        except Exception:
            logger.exception('Failed migrating password hash for login=%s', login)

    try:
        auth_payload, payload_error = _build_auth_payload(user_data)
        if payload_error:
            return None, payload_error
        return auth_payload, None
    except Exception:
        logger.exception('Token generation failed for user_id=%s', user_data.get('matricula'))
        return None, 'Erro de autenticacao.'


def get_all_users(limit: int = 100, offset: int = 0):
    """Return active users with pagination."""
    conn = db_manager.connect()
    if not conn:
        return [], 'Erro de conexao com o banco de dados.'

    try:
        cursor = conn.cursor()
        sql_query = """
            SELECT
                t.matricula,
                t.nome
            FROM pcempr t
            WHERE t.situacao = 'A'
              AND t.dt_exclusao IS NULL
              AND t.dtdemissao IS NULL
            ORDER BY t.nome ASC
            OFFSET :offset ROWS FETCH NEXT :limit ROWS ONLY
        """
        cursor.execute(sql_query, offset=int(offset), limit=int(limit))
        users = cursor.fetchall()

        column_names = ['id', 'name']
        users_list = [dict(zip(column_names, user)) for user in users]
        return users_list, None

    except cx_Oracle.DatabaseError:
        logger.exception('Database error while fetching users list')
        return [], 'Erro interno ao buscar usuarios.'
    finally:
        if conn:
            conn.close()


def search_users(query, search_by, limit: int = 100, offset: int = 0):
    """Search active users by matricula or nome with pagination."""
    conn = db_manager.connect()
    if not conn:
        return [], 'Erro de conexao com o banco de dados.'

    try:
        cursor = conn.cursor()
        sql_query = """
            SELECT
                t.matricula,
                t.nome
            FROM pcempr t
            WHERE t.situacao = 'A'
              AND t.dt_exclusao IS NULL
              AND t.dtdemissao IS NULL
        """
        params = {'offset': int(offset), 'limit': int(limit)}

        if search_by == 'matricula':
            sql_query += ' AND t.matricula = :query'
            params['query'] = query
        elif search_by == 'name':
            sql_query += ' AND UPPER(t.nome) LIKE UPPER(:query)'
            params['query'] = f'%{query}%'
        else:
            return [], "Tipo de busca invalido. Use 'matricula' ou 'name'."

        sql_query += ' ORDER BY t.nome ASC OFFSET :offset ROWS FETCH NEXT :limit ROWS ONLY'

        cursor.execute(sql_query, params)
        users = cursor.fetchall()

        column_names = ['id', 'name']
        users_list = [dict(zip(column_names, user)) for user in users]
        return users_list, None

    except cx_Oracle.DatabaseError:
        logger.exception('Database error while searching users')
        return [], 'Erro interno ao buscar usuarios.'
    finally:
        if conn:
            conn.close()
