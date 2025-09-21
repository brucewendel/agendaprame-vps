import requests
import json
from datetime import datetime, timedelta

# --- Configurações ---
BASE_URL = "http://127.0.0.1:5000"
# ATENÇÃO: Substitua com credenciais válidas do seu ambiente
ADMIN_CREDENTIALS = {"login": "admin", "senha": "admin_password"}
USER_CREDENTIALS = {"login": "user", "senha": "user_password"}

# --- Variáveis Globais ---
admin_token = None
user_token = None
created_room_id = None

# --- Funções Auxiliares ---
def print_test_title(title):
    print(f"\n{'='*40}\n{title}\n{'='*40}")

def print_result(success, message):
    status = "SUCCESS" if success else "FAILURE"
    print(f"[{status}] - {message}")
    return success

# --- Testes de API ---
def test_login():
    """Testa o login de admin e usuário."""
    global admin_token, user_token
    print_test_title("1. Teste de Login")
    admin_success = False
    user_success = False

    try:
        response = requests.post(f"{BASE_URL}/login", json=ADMIN_CREDENTIALS)
        if response.status_code == 200:
            admin_token = response.json()['token']
            admin_success = print_result(True, f"Login de admin bem-sucedido.")
        else:
            admin_success = print_result(False, f"Falha no login de admin. Status: {response.status_code}, Resposta: {response.text}")
    except requests.exceptions.ConnectionError as e:
        admin_success = print_result(False, f"Erro de conexão ao tentar logar como admin: {e}")

    try:
        response = requests.post(f"{BASE_URL}/login", json=USER_CREDENTIALS)
        if response.status_code == 200:
            user_token = response.json()['token']
            user_success = print_result(True, f"Login de usuário bem-sucedido.")
        else:
            user_success = print_result(False, f"Falha no login de usuário. Status: {response.status_code}, Resposta: {response.text}")
    except requests.exceptions.ConnectionError as e:
        user_success = print_result(False, f"Erro de conexão ao tentar logar como usuário: {e}")
    
    return admin_success and user_success

def test_room_creation():
    """Testa a criação de uma nova sala (requer admin)."""
    global created_room_id
    print_test_title("2. Teste de Criação de Sala (Admin)")
    if not admin_token:
        return print_result(False, "Token de admin não disponível. Pulando teste.")

    headers = {"Authorization": f"Bearer {admin_token}"}
    room_data = {"name": "Sala de Teste Automatizado"}

    try:
        response = requests.post(f"{BASE_URL}/rooms", headers=headers, json=room_data)
        if response.status_code == 201:
            created_room_id = response.json()['id']
            return print_result(True, f"Sala criada com sucesso. ID: {created_room_id}")
        else:
            return print_result(False, f"Falha ao criar sala. Status: {response.status_code}, Resposta: {response.text}")
    except requests.exceptions.ConnectionError as e:
        return print_result(False, f"Erro de conexão ao criar sala: {e}")

def test_get_all_rooms():
    """Testa a listagem de todas as salas."""
    print_test_title("3. Teste de Listagem de Salas")
    if not user_token:
        return print_result(False, "Token de usuário não disponível. Pulando teste.")

    headers = {"Authorization": f"Bearer {user_token}"}
    try:
        response = requests.get(f"{BASE_URL}/rooms", headers=headers)
        if response.status_code == 200:
            return print_result(True, f"Salas listadas com sucesso. Total: {len(response.json())}")
        else:
            return print_result(False, f"Falha ao listar salas. Status: {response.status_code}, Resposta: {response.text}")
    except requests.exceptions.ConnectionError as e:
        return print_result(False, f"Erro de conexão ao listar salas: {e}")

def test_booking_creation():
    """Testa a criação de um agendamento."""
    print_test_title("4. Teste de Criação de Agendamento")
    if not user_token or not created_room_id:
        return print_result(False, "Token de usuário ou ID da sala não disponível. Pulando teste.")

    headers = {"Authorization": f"Bearer {user_token}"}
    start_time = datetime.now() + timedelta(days=1)
    end_time = start_time + timedelta(hours=1)
    booking_data = {
        "sala_id": created_room_id,
        "inicio": start_time.isoformat(),
        "fim": end_time.isoformat(),
        "titulo": "Reunião de Teste Automatizado",
        "descricao": "Discussão sobre os testes da API."
    }

    try:
        response = requests.post(f"{BASE_URL}/agendamentos", headers=headers, json=booking_data)
        if response.status_code == 201:
            return print_result(True, "Agendamento criado com sucesso.")
        else:
            return print_result(False, f"Falha ao criar agendamento. Status: {response.status_code}, Resposta: {response.text}")
    except requests.exceptions.ConnectionError as e:
        return print_result(False, f"Erro de conexão ao criar agendamento: {e}")

def test_room_deactivation():
    """Testa a desativação de uma sala (requer admin)."""
    print_test_title("5. Teste de Desativação de Sala (Admin)")
    if not admin_token or not created_room_id:
        return print_result(False, "Token de admin ou ID da sala não disponível. Pulando teste.")

    headers = {"Authorization": f"Bearer {admin_token}"}
    update_data = {"active": False}

    try:
        response = requests.put(f"{BASE_URL}/rooms/{created_room_id}", headers=headers, json=update_data)
        if response.status_code == 200 and response.json()['active'] is False:
            return print_result(True, f"Sala {created_room_id} desativada com sucesso.")
        else:
            return print_result(False, f"Falha ao desativar sala. Status: {response.status_code}, Resposta: {response.text}")
    except requests.exceptions.ConnectionError as e:
        return print_result(False, f"Erro de conexão ao desativar sala: {e}")

def test_room_deletion():
    """Testa a exclusão de uma sala (requer admin)."""
    print_test_title("6. Teste de Exclusão de Sala (Admin)")
    if not admin_token or not created_room_id:
        return print_result(False, "Token de admin ou ID da sala não disponível. Pulando teste.")

    headers = {"Authorization": f"Bearer {admin_token}"}

    try:
        response = requests.delete(f"{BASE_URL}/rooms/{created_room_id}", headers=headers)
        if response.status_code == 200:
            return print_result(True, f"Sala {created_room_id} excluída com sucesso.")
        else:
            return print_result(False, f"Falha ao excluir sala. Status: {response.status_code}, Resposta: {response.text}")
    except requests.exceptions.ConnectionError as e:
        return print_result(False, f"Erro de conexão ao excluir sala: {e}")

def print_summary(results):
    """Imprime o resumo dos testes."""
    print_test_title("Resumo dos Testes")
    failures = {test: result for test, result in results.items() if not result}
    
    if not failures:
        print("\033[92mSUCESSO! Todos os testes passaram.\033[0m")
    else:
        print("\033[91mFALHA! Alguns testes não passaram.\033[0m")
        print("\nFuncionalidades com erro:")
        for test_name in failures:
            print(f"- {test_name}")

# --- Execução dos Testes ---
if __name__ == "__main__":
    print("Iniciando suíte de testes da API de Agendamento de Salas...")
    print("Certifique-se de que o servidor backend está rodando em http://127.0.0.1:5000")
    print("E que as credenciais de ADMIN e USER estão corretas neste script.")

    test_results = {}
    
    # Executa os testes em sequência e armazena os resultados
    test_results["Login"] = test_login()
    # A criação da sala depende do login de admin
    if admin_token:
        test_results["Criação de Sala"] = test_room_creation()
    else:
        test_results["Criação de Sala"] = False

    test_results["Listagem de Salas"] = test_get_all_rooms()
    
    # O agendamento depende da criação da sala
    if created_room_id:
        test_results["Criação de Agendamento"] = test_booking_creation()
    else:
        test_results["Criação de Agendamento"] = False

    # A desativação depende da criação da sala
    if created_room_id:
        test_results["Desativação de Sala"] = test_room_deactivation()
    else:
        test_results["Desativação de Sala"] = False

    # A exclusão depende da criação da sala
    if created_room_id:
        test_results["Exclusão de Sala"] = test_room_deletion()
    else:
        test_results["Exclusão de Sala"] = False

    print_summary(test_results)

    print("\nFim da suíte de testes.")