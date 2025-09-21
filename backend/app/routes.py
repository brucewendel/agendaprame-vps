from flask import Blueprint, request, jsonify
from utils.auth_decorators import jwt_required, admin_required
from services.room_service import room_service
from services import auth_service, booking_service

main = Blueprint('main', __name__)

@main.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or 'login' not in data or 'senha' not in data:
        return jsonify({"message": "Dados de login incompletos."}), 400

    login = data['login']
    senha = data['senha']
    auth_data, error = auth_service.authenticate_user(login, senha)
    if error:
        return jsonify({"message": error}), 401

    return jsonify({
        "message": "Autenticação bem-sucedida.",
        "token": auth_data['token'],
        "profile": auth_data['profile'],
        "name": auth_data['name']
    }), 200

# --- Rotas de Salas (CRUD - Admin) ---
@main.route('/rooms', methods=['POST'])
@jwt_required
@admin_required
def create_room():
    data = request.get_json()
    if not data or 'name' not in data:
        return jsonify({"message": "Nome da sala é obrigatório."}), 400
    
    room, error = room_service.create_room(data['name'])
    if error:
        return jsonify({"message": error}), 400
    return jsonify({"id": room.id, "name": room.name, "active": room.active}), 201

@main.route('/rooms', methods=['GET'])
@jwt_required
def get_all_rooms():
    rooms, error = room_service.get_all_rooms()
    if error:
        return jsonify({"message": error}), 500
    return jsonify([{"id": room.id, "name": room.name, "active": room.active} for room in rooms]), 200

@main.route('/rooms/<int:room_id>', methods=['GET'])
@jwt_required
def get_room(room_id):
    room, error = room_service.get_room_by_id(room_id)
    if error:
        return jsonify({"message": error}), 404
    return jsonify({"id": room.id, "name": room.name, "active": room.active}), 200

@main.route('/rooms/<int:room_id>', methods=['PUT'])
@jwt_required
@admin_required
def update_room(room_id):
    data = request.get_json()
    if not data:
        return jsonify({"message": "Nenhum dado fornecido para atualização."}), 400
    
    name = data.get('name')
    active = data.get('active')

    if name is None and active is None:
        return jsonify({"message": "Pelo menos 'name' ou 'active' deve ser fornecido para atualização."}), 400

    # Fetch existing room to get current values if not provided in the request
    existing_room, error = room_service.get_room_by_id(room_id)
    if error:
        return jsonify({"message": error}), 404

    if name is None:
        name = existing_room.name
    if active is None:
        active = existing_room.active

    room, error = room_service.update_room(room_id, name, active)
    if error:
        return jsonify({"message": error}), 400
    return jsonify({"id": room.id, "name": room.name, "active": room.active}), 200

@main.route('/rooms/<int:room_id>', methods=['DELETE'])
@jwt_required
@admin_required
def delete_room(room_id):
    success, error = room_service.delete_room(room_id)
    if error:
        return jsonify({"message": error}), 400
    return jsonify({"message": "Sala excluída com sucesso."}), 200


# --- Rotas de Agendamentos (Funcionalidades Principais) ---
@main.route('/agendamentos', methods=['POST'])
@jwt_required
def create_booking():
    data = request.get_json()
    user_id = request.user_id
    if not data or 'sala_id' not in data or 'inicio' not in data or 'fim' not in data:
        return jsonify({"message": "Dados de agendamento incompletos."}), 400
    booking, error = booking_service.create_booking(data, user_id)
    if error:
        return jsonify({"message": error}), 409
    return jsonify(booking), 201

@main.route('/agendamentos', methods=['GET'])
@jwt_required
def get_bookings():
    start = request.args.get('start')
    end = request.args.get('end')
    bookings_list, error = booking_service.get_bookings(start, end)
    if error:
        return jsonify({"message": error}), 500
    return jsonify(bookings_list), 200

@main.route('/agendamentos/<int:booking_id>', methods=['PUT'])
@jwt_required
def update_booking(booking_id):
    data = request.get_json()
    user_id = request.user_id
    user_profile = request.profile
    booking, error = booking_service.update_booking(booking_id, data, user_id, user_profile)
    if error:
        return jsonify({"message": error}), 400
    return jsonify(booking), 200

@main.route('/agendamentos/<int:booking_id>', methods=['DELETE'])
@jwt_required
def delete_booking(booking_id):
    user_id = request.user_id
    user_profile = request.profile
    success, error = booking_service.delete_booking(booking_id, user_id, user_profile)
    if error:
        return jsonify({"message": error}), 400
    return jsonify({"message": "Agendamento cancelado com sucesso."}), 200

@main.route('/agendamentos/<int:id_agendamento>', methods=['GET'])
@jwt_required
def get_agendamento(id_agendamento):
    agendamento, error = booking_service.get_agendamento(id_agendamento)
    if error or not agendamento:
        return jsonify({"message": "Agendamento não encontrado."}), 404
    return jsonify(agendamento), 200