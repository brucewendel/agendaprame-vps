from flask import Blueprint, request, jsonify, current_app

from utils.auth_decorators import jwt_required, admin_required
from utils.login_rate_limiter import LoginRateLimiter
from services.room_service import room_service
from services import auth_service, booking_service

main = Blueprint('main', __name__)
_login_rate_limiter = None


def _get_login_limiter() -> LoginRateLimiter:
    global _login_rate_limiter
    if _login_rate_limiter is None:
        _login_rate_limiter = LoginRateLimiter(
            max_attempts=current_app.config.get('LOGIN_MAX_ATTEMPTS', 5),
            window_seconds=current_app.config.get('LOGIN_WINDOW_SECONDS', 600),
            block_seconds=current_app.config.get('LOGIN_BLOCK_SECONDS', 900),
        )
    return _login_rate_limiter


def _get_client_ip() -> str:
    forwarded_for = request.headers.get('X-Forwarded-For', '')
    if forwarded_for:
        return forwarded_for.split(',')[0].strip()
    return request.remote_addr or 'unknown'


@main.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or 'login' not in data or 'senha' not in data:
        return jsonify({'message': 'Dados de login incompletos.'}), 400

    login_value = data['login']
    senha = data['senha']

    rate_limiter = _get_login_limiter()
    rate_limit_key = f"{_get_client_ip()}|{str(login_value).upper()}"

    blocked, retry_after = rate_limiter.is_blocked(rate_limit_key)
    if blocked:
        return jsonify({
            'message': 'Muitas tentativas de login. Tente novamente em instantes.',
            'retry_after_seconds': retry_after,
        }), 429

    auth_data, error = auth_service.authenticate_user(login_value, senha)
    if error:
        rate_limiter.register_failure(rate_limit_key)
        return jsonify({'message': 'Credenciais inválidas.'}), 401

    rate_limiter.register_success(rate_limit_key)
    return jsonify({
        'message': 'Autenticacao bem-sucedida.',
        'token': auth_data['token'],
        'profile': auth_data['profile'],
        'name': auth_data['name'],
    }), 200


@main.route('/users', methods=['GET'])
@jwt_required
@admin_required
def get_users():
    limit = min(max(request.args.get('limit', default=100, type=int) or 100, 1), 500)
    offset = max(request.args.get('offset', default=0, type=int) or 0, 0)

    users, error = auth_service.get_all_users(limit=limit, offset=offset)
    if error:
        return jsonify({'message': error}), 500
    return jsonify(users), 200


@main.route('/users/search', methods=['GET'])
@jwt_required
@admin_required
def search_users_route():
    query = request.args.get('query')
    search_by = request.args.get('search_by')
    limit = min(max(request.args.get('limit', default=100, type=int) or 100, 1), 500)
    offset = max(request.args.get('offset', default=0, type=int) or 0, 0)

    if not query or not search_by:
        return jsonify({'message': "Parametros de busca 'query' e 'search_by' sao obrigatorios."}), 400

    users, error = auth_service.search_users(query, search_by, limit=limit, offset=offset)
    if error:
        return jsonify({'message': error}), 500
    return jsonify(users), 200


# --- Rotas de Salas (CRUD - Admin) ---
@main.route('/rooms', methods=['POST'])
@jwt_required
@admin_required
def create_room():
    data = request.get_json()
    if not data or 'name' not in data:
        return jsonify({'message': 'Nome da sala e obrigatorio.'}), 400

    room, error = room_service.create_room(data['name'])
    if error:
        return jsonify({'message': error}), 400
    return jsonify({'id': room.id, 'name': room.name, 'active': room.active}), 201


@main.route('/rooms', methods=['GET'])
@jwt_required
def get_all_rooms():
    rooms, error = room_service.get_all_rooms()
    if error:
        return jsonify({'message': error}), 500
    return jsonify([{'id': room.id, 'name': room.name, 'active': room.active} for room in rooms]), 200


@main.route('/rooms/<int:room_id>', methods=['GET'])
@jwt_required
def get_room(room_id):
    room, error = room_service.get_room_by_id(room_id)
    if error:
        return jsonify({'message': error}), 404
    return jsonify({'id': room.id, 'name': room.name, 'active': room.active}), 200


@main.route('/rooms/<int:room_id>', methods=['PUT'])
@jwt_required
@admin_required
def update_room(room_id):
    data = request.get_json()
    if not data:
        return jsonify({'message': 'Nenhum dado fornecido para atualizacao.'}), 400

    name = data.get('name')
    active = data.get('active')

    if name is None and active is None:
        return jsonify({'message': "Pelo menos 'name' ou 'active' deve ser fornecido para atualizacao."}), 400

    existing_room, error = room_service.get_room_by_id(room_id)
    if error:
        return jsonify({'message': error}), 404

    if name is None:
        name = existing_room.name
    if active is None:
        active = existing_room.active

    room, error = room_service.update_room(room_id, name, active)
    if error:
        return jsonify({'message': error}), 400
    return jsonify({'id': room.id, 'name': room.name, 'active': room.active}), 200


@main.route('/rooms/<int:room_id>', methods=['DELETE'])
@jwt_required
@admin_required
def delete_room(room_id):
    success, error = room_service.delete_room(room_id)
    if error:
        return jsonify({'message': error}), 400
    return jsonify({'message': 'Sala excluida com sucesso.'}), 200


# --- Rotas de Agendamentos (Funcionalidades Principais) ---
@main.route('/agendamentos', methods=['POST'])
@jwt_required
def create_booking():
    data = request.get_json()
    user_id = request.user_id
    if not data or 'sala_id' not in data or 'inicio' not in data or 'fim' not in data:
        return jsonify({'message': 'Dados de agendamento incompletos.'}), 400

    booking, error = booking_service.create_booking(data, user_id)
    if error:
        return jsonify({'message': error}), 409
    return jsonify(booking), 201


@main.route('/agendamentos', methods=['GET'])
@jwt_required
def get_bookings():
    start = request.args.get('start')
    end = request.args.get('end')
    bookings_list, error = booking_service.get_bookings(start, end)
    if error:
        return jsonify({'message': error}), 500
    return jsonify(bookings_list), 200


@main.route('/agendamentos/<int:booking_id>', methods=['PUT'])
@jwt_required
def update_booking(booking_id):
    data = request.get_json()
    user_id = request.user_id
    user_profile = request.profile

    booking, error = booking_service.update_booking(booking_id, data, user_id, user_profile)
    if error:
        return jsonify({'message': error}), 400
    return jsonify(booking), 200


@main.route('/agendamentos/<int:booking_id>', methods=['DELETE'])
@jwt_required
def delete_booking(booking_id):
    user_id = request.user_id
    user_profile = request.profile

    success, error = booking_service.delete_booking(booking_id, user_id, user_profile)
    if error:
        return jsonify({'message': error}), 400
    return jsonify({'message': 'Agendamento cancelado com sucesso.'}), 200


@main.route('/agendamentos/<int:id_agendamento>', methods=['GET'])
@jwt_required
def get_agendamento(id_agendamento):
    agendamento, error = booking_service.get_agendamento(id_agendamento)
    if error or not agendamento:
        return jsonify({'message': 'Agendamento nao encontrado.'}), 404
    return jsonify(agendamento), 200
