import logging
import os
import threading

import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')
# ID do cargo (role) de suporte. Para usuario, use <@ID>.
SUPPORT_MENTION = os.getenv('DISCORD_SUPPORT_MENTION', '<@&1339309327768485982>')

_COLORS = {'create': 0x2ECC71, 'update': 0xF1C40F, 'delete': 0xE74C3C}
_TITLES = {
    'create': 'Novo agendamento de sala',
    'update': 'Agendamento alterado',
    'delete': 'Agendamento cancelado',
}


def needs_support(descricao) -> bool:
    return 'suporte de ti' in (descricao or '').lower()


def _fmt(dt):
    return dt.strftime('%d/%m/%Y %H:%M') if hasattr(dt, 'strftime') else str(dt)


def _post(payload):
    try:
        resp = requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=10)
        resp.raise_for_status()
    except Exception:
        logger.warning('Falha ao enviar notificacao para o Discord.', exc_info=True)


def notify_booking(action, sala, titulo, inicio, fim, user_name=None, descricao=None):
    """Envia (em background) uma notificacao de agendamento ao Discord.

    action: 'create' | 'update' | 'delete'. Marca o suporte quando a
    descricao contem a opcao "Suporte de TI". Nunca levanta excecao.
    """
    if not DISCORD_WEBHOOK_URL:
        logger.warning('DISCORD_WEBHOOK_URL nao configurada; notificacao Discord ignorada.')
        return

    try:
        fields = [
            {'name': 'Sala', 'value': str(sala or '-'), 'inline': True},
            {'name': 'Responsavel', 'value': (user_name or '-').strip() or '-', 'inline': True},
            {'name': 'Titulo', 'value': str(titulo or '-')[:1024], 'inline': False},
            {'name': 'Inicio', 'value': _fmt(inicio), 'inline': True},
            {'name': 'Fim', 'value': _fmt(fim), 'inline': True},
        ]
        if descricao:
            fields.append({'name': 'Detalhes', 'value': str(descricao)[:1024], 'inline': False})

        support = needs_support(descricao)
        payload = {
            'content': f'{SUPPORT_MENTION} Suporte de TI solicitado.' if support else '',
            'embeds': [{'title': _TITLES[action], 'color': _COLORS[action], 'fields': fields}],
            'allowed_mentions': {'parse': ['users', 'roles']} if support else {'parse': []},
        }
        threading.Thread(target=_post, args=(payload,), daemon=True).start()
    except Exception:
        logger.warning('Falha ao montar notificacao Discord.', exc_info=True)
