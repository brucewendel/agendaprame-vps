import jwt
import os
from datetime import datetime, timedelta
from utils.db_conection import db_manager


def authenticate_user(login, senha_fornecida):
    """
    Autentica um usuário usando o login e a senha fornecida.
    A validação da senha é feita com base na senha descriptografada retornada do banco.
    """
    user_data, error = db_manager.get_user_data_from_db(login)
    
    if error:
        return None, error

    if not user_data:
        return None, "Usuário não encontrado."
    
    # Os dados retornados da query agora são: matricula, nome, usuariobd, senha_descriptografada, codsetor, dt_exclusao, situacao, dtdemissao
    matricula, nome, usuariobd, senha_descriptografada, codsetor, dt_exclusao, situacao, dtdemissao = user_data

    # Validação de usuário ativo
    if situacao != 'A' or dt_exclusao is not None or dtdemissao is not None:
        return None, "Usuário inativo ou excluído."

    print(f"Senha fornecida: {senha_fornecida}")
    print(f"Senha descriptografada do BD: {senha_descriptografada}")

    # Realiza a comparação direta da senha fornecida com a senha descriptografada
    if str(senha_descriptografada) != str(senha_fornecida):
        print('senhas diferentes')
        return None, "Senha incorreta."
    
    print("Senhas iguais, prosseguindo para gerar token...")
    # Se a senha for válida, crie um token JWT
    try:
        # Define o perfil do usuário com base no CODSETOR
        if codsetor == 15:
            perfil = "Administrador"
        else:
            perfil = "Funcionario"

        payload = {
            'user_id': matricula, # Usamos a matricula como ID do usuário no token
            'profile': perfil,
            'exp': datetime.utcnow() + timedelta(days=1)  # Token expira em 1 dia
        }
        token = jwt.encode(payload, os.environ.get('SECRET_KEY'), algorithm='HS256')
        
        return {
            "token": token,
            "profile": perfil,
            "name": nome
        }, None
    except Exception as e:
        return None, f"Erro ao gerar o token: {str(e)}"

def get_all_users():
    """
    Retorna uma lista de todos os usuários ativos.
    """
    conn = db_manager.connect()
    if not conn:
        return [], "Erro de conexão com o banco de dados."

    try:
        cursor = db_manager.connection.cursor()
        
        sql_query = """
            SELECT
                t.matricula,
                t.nome
            FROM pcempr t
            WHERE t.situacao = 'A' AND t.dt_exclusao IS NULL AND t.dtdemissao IS NULL
            ORDER BY t.nome ASC
        """
        
        cursor.execute(sql_query)
        users = cursor.fetchall()

        # Renomeia as colunas para um formato mais amigável para o frontend
        column_names = ['id', 'name'] 
        users_list = [dict(zip(column_names, user)) for user in users]

        return users_list, None

    except cx_Oracle.DatabaseError as e:
        error, = e.args
        return [], f"Erro ao buscar usuários: {error.message}"
    
    finally:
        if conn:
            db_manager.connection.close()

def search_users(query, search_by):
    """
    Busca usuários ativos por matrícula ou nome.
    """
    conn = db_manager.connect()
    if not conn:
        return [], "Erro de conexão com o banco de dados."

    try:
        cursor = db_manager.connection.cursor()
        
        sql_query = """
            SELECT
                t.matricula,
                t.nome
            FROM pcempr t
            WHERE t.situacao = 'A' AND t.dt_exclusao IS NULL AND t.dtdemissao IS NULL
        """
        params = {}

        if search_by == 'matricula':
            sql_query += " AND t.matricula = :query"
            params['query'] = query
        elif search_by == 'name':
            sql_query += " AND UPPER(t.nome) LIKE UPPER(:query)"
            params['query'] = f"%{query}%"
        else:
            return [], "Tipo de busca inválido. Use 'matricula' ou 'name'."
        
        sql_query += " ORDER BY t.nome ASC"

        cursor.execute(sql_query, params)
        users = cursor.fetchall()

        column_names = ['id', 'name'] 
        users_list = [dict(zip(column_names, user)) for user in users]

        return users_list, None

    except cx_Oracle.DatabaseError as e:
        error, = e.args
        return [], f"Erro ao buscar usuários: {error.message}"
    
    finally:
        if conn:
            db_manager.connection.close()