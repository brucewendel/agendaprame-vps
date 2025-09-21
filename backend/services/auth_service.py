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