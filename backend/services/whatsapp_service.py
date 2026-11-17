import logging
import os
import threading

import requests
from dotenv import load_dotenv

from services.discord_service import needs_support

load_dotenv()

logger = logging.getLogger(__name__)

# Mesma API/numero oficial da MX2Tech usada pelo MXCOB para enviar OTP (MYZAPI).
WHATSAPP_API_URL = os.getenv('WHATSAPP_API_URL')
WHATSAPP_API_TOKEN = os.getenv('WHATSAPP_API_TOKEN')
SUPPORT_ALERT_PHONE = os.getenv('SUPPORT_ALERT_PHONE', '85992126661')

_TITLES = {
    'create': 'Novo agendamento com Suporte de TI',
    'update': 'Agendamento com Suporte de TI alterado',
    'delete': 'Agendamento com Suporte de TI cancelado',
}


def _format_phone(phone):
    digits = ''.join(ch for ch in str(phone or '') if ch.isdigit())
    if len(digits) in (10, 11):
        digits = '55' + digits
    return digits


def _fmt(dt):
    return dt.strftime('%d/%m/%Y %H:%M') if hasattr(dt, 'strftime') else str(dt)


def _post(url, token, payload):
    try:
        resp = requests.post(
            url,
            headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
            json=payload,
            timeout=15,
        )
        resp.raise_for_status()
    except Exception:
        logger.warning('Falha ao enviar alerta de suporte por WhatsApp.', exc_info=True)


def notify_support(action, sala, titulo, inicio, fim, user_name=None, descricao=None):
    """Envia (em background) alerta de WhatsApp ao suporte quando o agendamento
    tem "Suporte de TI". Nunca levanta excecao."""
    try:
        if not needs_support(descricao):
            return
        phone = _format_phone(SUPPORT_ALERT_PHONE)
        if not (WHATSAPP_API_URL and WHATSAPP_API_TOKEN and phone):
            logger.warning('WhatsApp de suporte nao configurado (WHATSAPP_API_URL/TOKEN); alerta ignorado.')
            return

        mensagem = (
            f'*{_TITLES[action]}*\n\n'
            f'Sala: {sala or "-"}\n'
            f'Responsavel: {(user_name or "-").strip() or "-"}\n'
            f'Titulo: {titulo or "-"}\n'
            f'Inicio: {_fmt(inicio)}\n'
            f'Fim: {_fmt(fim)}\n\n'
            f'{descricao or ""}'
        )
        payload = {'number': phone, 'message': mensagem, 'createTicket': 'false'}
        threading.Thread(
            target=_post, args=(WHATSAPP_API_URL, WHATSAPP_API_TOKEN, payload), daemon=True
        ).start()
    except Exception:
        logger.warning('Falha ao montar alerta WhatsApp de suporte.', exc_info=True)
