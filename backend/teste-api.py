import requests
import json
from datetime import datetime, timedelta

# --- Configuração da API ---
BASE_URL = "http://127.0.0.1:5000"

# Credenciais de login para o teste
LOGIN_PAYLOAD = {
    "login": "PCADMIN",
    "senha": "NAOMEXA"
}

# Dados para o agendamento de teste (payload 1)
BOOKING_PAYLOAD = {
    "sala_id": 1,
    "inicio": "2025-09-18T10:00:00",
    "fim": "2025-09-18T11:00:00",
    "titulo": "Reuniao de Teste",
    "descricao": "Teste de criacao de agendamento via script."
}

# Dados para o teste de conflito (payload 2 - mesmo horário)
CONFLICT_PAYLOAD = {
    "sala_id": 1,
    "inicio": "2025-09-18T10:00:00",
    "fim": "2025-09-18T11:00:00",
    "titulo": "Reuniao de Teste de Conflito",
    "descricao": "Teste de criacao de agendamento via script."
}

# Variáveis para armazenar o token e o ID do agendamento
auth_token = None
booking_id = None

# --- Funções de Teste ---

def run_test(test_name, method, endpoint, headers=None, payload=None, expected_status=200):
    """Função utilitária para executar e imprimir o resultado de cada teste."""
    global booking_id
    print(f"\n--- [Testando: {test_name}] ---")
    url = f"{BASE_URL}/{endpoint}"
    
    try:
        response = requests.request(method, url, headers=headers, json=payload)
        status_code = response.status_code
        
        if status_code == expected_status:
            print(f"  ✔ Sucesso! Status: {status_code} - {response.reason}")
            try:
                json_response = response.json()
                print("  Resposta:", json.dumps(json_response, indent=2))
                # Captura o ID para os próximos testes
                if 'id_agendamento' in json_response:
                    booking_id = json_response['id_agendamento']
            except json.JSONDecodeError:
                print("  Resposta:", response.text)
        else:
            print(f"  ✖ Falha! Status inesperado: {status_code} (esperado: {expected_status})")
            print("  Resposta:", response.text)
            return None
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"  ✖ Erro na requisição: {e}")
        return None

def main():
    global auth_token, booking_id
    
    # 1. Teste de Autenticação
    login_response = run_test("Autenticação", "POST", "login", payload=LOGIN_PAYLOAD, expected_status=200)
    if login_response:
        auth_token = login_response.get('token')
        headers = {"Authorization": f"Bearer {auth_token}"}
    else:
        return # Encerra se a autenticação falhar

    # 2. Teste de Criação de Agendamento
    create_response = run_test("Criação de Agendamento", "POST", "agendamentos", headers=headers, payload=BOOKING_PAYLOAD, expected_status=201)
    if create_response:
        booking_id = create_response.get('id_agendamento')

    # 3. Teste de Conflito (Agendamento Duplicado)
    run_test("Checagem de Conflito", "POST", "agendamentos", headers=headers, payload=CONFLICT_PAYLOAD, expected_status=409)

    # 4. Teste de Visualização
    run_test("Visualização de Agendamentos", "GET", "agendamentos", headers=headers, expected_status=200)

    if booking_id:
        # A CORREÇÃO ESTÁ AQUI: Convertendo o ID para int
        booking_id = int(booking_id)

        # 5. Teste de Alteração de Agendamento
        updated_payload = BOOKING_PAYLOAD.copy()
        updated_payload['titulo'] = "Reuniao de Teste (ALTERADA)"
        updated_payload['inicio'] = "2025-09-18T11:00:00"
        updated_payload['fim'] = "2025-09-18T12:00:00"
        
        run_test(f"Alteração de Agendamento (ID: {booking_id})", "PUT", f"agendamentos/{booking_id}", headers=headers, payload=updated_payload, expected_status=200)

        # 6. Teste de Exclusão de Agendamento
        run_test(f"Exclusão de Agendamento (ID: {booking_id})", "DELETE", f"agendamentos/{booking_id}", headers=headers, expected_status=200)

        # 7. Confirmação de Exclusão (deve dar erro 400 ou 404)
        run_test(f"Confirmação de Exclusão", "GET", f"agendamentos/{booking_id}", headers=headers, expected_status=404)
    else:
        print("\nNão foi possível rodar os testes de Alteração e Exclusão pois o agendamento inicial não foi criado.")

if __name__ == "__main__":
    main()