import os
from functools import wraps

import jwt
from flask import request, jsonify


def jwt_required(f):
    """Validate JWT token from Authorization: Bearer <token>."""

    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '').strip()
        if not auth_header:
            return jsonify({'message': 'Token de autenticacao nao fornecido.'}), 401

        parts = auth_header.split(' ', 1)
        if len(parts) != 2 or parts[0].lower() != 'bearer' or not parts[1].strip():
            return jsonify({'message': 'Formato do token invalido.'}), 401

        token = parts[1].strip()
        secret_key = os.environ.get('SECRET_KEY')
        if not secret_key:
            return jsonify({'message': 'Configuracao de autenticacao invalida.'}), 500

        try:
            payload = jwt.decode(token, secret_key, algorithms=['HS256'])
            request.user_id = payload['user_id']
            request.profile = payload['profile']
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token de autenticacao expirado.'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Token de autenticacao invalido.'}), 401

        return f(*args, **kwargs)

    return decorated


def admin_required(f):
    """Allow route access only for admin profile users."""

    @wraps(f)
    def decorated(*args, **kwargs):
        if request.profile != 'Administrador':
            return jsonify({'message': 'Acesso nao autorizado para este perfil.'}), 403
        return f(*args, **kwargs)

    return decorated
