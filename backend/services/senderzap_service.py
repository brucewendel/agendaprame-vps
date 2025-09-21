import os
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

RECEPTION_PHONE = os.getenv('RECEPTION_WHATSAPP_NUMBER')
IT_PHONE = os.getenv('IT_WHATSAPP_NUMBER')

def send_whatsapp_message(to_number, message):
    """
    Função para enviar uma mensagem de WhatsApp.
    Esta é uma simulação. Você deve substituir o conteúdo desta função
    pela lógica de integração real com a sua API senderzap.
    """
    if not to_number:
        print(f"AVISO: Número de WhatsApp não configurado no arquivo .env para um dos destinatários.")
        return

    print("\n--- SIMULANDO ENVIO DE WHATSAPP ---")
    print(f"Para: {to_number}")
    print(f"Mensagem: {message}")
    print("------------------------------------\n")
    
    # Exemplo de como poderia ser a chamada real com a biblioteca 'requests':
    # try:
    #     import requests
    #     api_url = "URL_DA_SUA_API_SENDERZAP"
    #     payload = { "api_key": os.getenv('SENDERZAP_API_KEY'), "number": to_number, "message": message }
    #     response = requests.post(api_url, json=payload)
    #     response.raise_for_status()
    # except Exception as e:
    #     print(f"Falha ao enviar mensagem para {to_number}: {e}")