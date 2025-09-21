import jwt
import os
from functools import wraps
from flask import request, jsonify

def jwt_required(f):
    """
    Decorador que valida um token JWT na requisição.
    Adiciona 'user_id' e 'profile' ao objeto 'request'.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        # O token é esperado no cabeçalho Authorization como 'Bearer <token>'
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                # Extrai o token removendo o prefixo 'Bearer '
                token = auth_header.split(" ")[1]
            except IndexError:
                return jsonify({"message": "Formato do token inválido."}), 401
        
        if not token:
            return jsonify({"message": "Token de autenticação não fornecido."}), 401

        try:
            # Decodifica e valida o token
            payload = jwt.decode(token, os.environ.get('SECRET_KEY'), algorithms=['HS256'])
            # Adiciona os dados do usuário ao objeto request
            request.user_id = payload['user_id']
            request.profile = payload['profile']
        except jwt.ExpiredSignatureError:
            return jsonify({"message": "Token de autenticação expirado."}), 401
        except jwt.InvalidTokenError:
            return jsonify({"message": "Token de autenticação inválido."}), 401

        return f(*args, **kwargs)

    return decorated

def admin_required(f):
    """
    Decorador que garante que apenas administradores podem acessar a rota.
    Deve ser usado após o decorador @jwt_required.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        # O decorador jwt_required já adicionou o perfil do usuário à requisição
        if request.profile != 'Administrador':
            return jsonify({"message": "Acesso não autorizado para este perfil."}), 403
        
        return f(*args, **kwargs)

    return decorated