import smtplib
import ssl
import logging
from pathlib import Path
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email import encoders
from datetime import datetime
from ics import Calendar, Event
from app.config import Config

logger = logging.getLogger(__name__)

# Caminho universal para o logo (assumindo estrutura: backend/services -> backend/img/logo.png)
CURRENT_DIR = Path(__file__).resolve().parent        # backend/services
BACKEND_DIR = CURRENT_DIR.parent                     # backend
LOGO_PATH = BACKEND_DIR / "img" / "logo.png"         # backend/img/logo.png


def _attach_logo_to_message(message_root):
    """
    Anexa o logo ao email (se existir). Usa multipart/related para garantir que o CID seja reconhecido.
    message_root deve ser o MIMEMultipart('related').
    """
    try:
        if LOGO_PATH.exists():
            with open(LOGO_PATH, "rb") as f:
                img = MIMEImage(f.read())
            img.add_header("Content-ID", "<logo>")
            img.add_header("Content-Disposition", "inline", filename="logo.png")
            message_root.attach(img)
            return True
        else:
            # se não existir, não anexa, mas não quebra
            return False
    except Exception:
        return False


def _get_smtp_settings():
    sender_email = Config.SMTP_USER
    sender_password = Config.SMTP_PASSWORD
    smtp_server = Config.SMTP_SERVER
    smtp_port = Config.SMTP_PORT

    if not sender_email or not sender_password or not smtp_server or not smtp_port:
        logger.error('SMTP settings are missing in environment variables.')
        return None

    return sender_email, sender_password, smtp_server, smtp_port


# 100% atualizado para envio de e-mails com convite .ics
def send_booking_confirmation(recipient_email, booking_details):
    """
    Gera um convite .ics e o envia por e-mail.

    :param recipient_email: E-mail do destinatário.
    :param booking_details: Dicionário com os detalhes do agendamento.
                            Precisa conter ao menos: 'dtstart', 'dtend'.
                            Pode conter: 'summary', 'description', 'location', 'user_name'.
    """
    smtp_settings = _get_smtp_settings()
    if not smtp_settings:
        return False
    sender_email, sender_password, smtp_server, smtp_port = smtp_settings

    # Criar o evento do calendário
    c = Calendar()
    e = Event()
    e.name = booking_details.get('summary', 'Agendamento de Sala')
    e.begin = booking_details.get('dtstart')
    e.end = booking_details.get('dtend')
    e.description = booking_details.get('description')
    e.location = booking_details.get('location')
    c.events.add(e)
    ics_content = str(c)

    # Criar estrutura multipart/related -> multipart/alternative (html) para suportar imagens inline
    message_root = MIMEMultipart("related")
    message_root["Subject"] = f"Confirmação de Agendamento: {e.name}"
    message_root["From"] = sender_email
    to_emails = [recipient_email, "ticket@mx2tech.com.br"]
    message_root["To"] = ", ".join(to_emails)

    # Parte alternativa (text + html)
    alt_part = MIMEMultipart("alternative")

    # Texto simples (fallback)
    plain_text = f"Confirmação de Agendamento: {e.name}\nInício: {e.begin}\nFim: {e.end}\nSala: {e.location}"
    alt_part.attach(MIMEText(plain_text, "plain"))

    # HTML (preservei exatamente como você forneceu)
    html = f"""
    <table style="background: #f9f9f9; margin: 0 auto; max-width: 600px; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.1); font-family: 'Segoe UI', Arial, sans-serif;">
        <tbody>
            <tr>
                <td>
                    <table style="background-color: #245de0;" width="100%" cellspacing="0" cellpadding="0">
                        <tbody>
                            <tr>
                                <td style="padding: 20px;" align="center"><img src="cid:logo" alt="image" width="80"></td>
                            </tr>
                            <tr>
                                <td style="padding: 0 20px 30px 20px;" align="center">
                                    <h1 style="color: white; margin: 0; font-size: 24px; font-weight: 600;">Agendamento Confirmado!</h1>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                    <table style="background: #ffffff;" width="100%" cellspacing="0" cellpadding="0">
                        <tbody>
                            <tr>
                                <td style="padding: 30px 25px 10px 25px;">
                                    <p style="margin: 0 0 15px 0; font-size: 16px; color: #374151; line-height: 1.6;"><span style="font-weight: 600; color: #2563eb;">Olá, {booking_details.get('user_name', '')}!</span><br>Seu agendamento foi confirmado com sucesso.</p>
                                    <div style="background: #f3f4f6; border-left: 4px solid #2563eb; padding: 15px; margin: 20px 0; border-radius: 0 8px 8px 0;">
                                        <p style="margin: 0; font-size: 15px; color: #4b5563; line-height: 1.6;">
                                            <strong>Título: {e.name}</strong><br>
                                            <strong>Sala:</strong> {e.location}<br>
                                            <strong>Início:</strong> {e.begin.strftime('%d/%m/%Y %H:%M')}<br>
                                            <strong>Fim:</strong> {e.end.strftime('%d/%m/%Y %H:%M')}<br>
                                            <strong>Descrição:</strong> {e.description or 'N/A'}
                                        </p>
                                    </div>
                                    <p style="margin: 0; font-size: 15px; color: #4b5563; line-height: 1.6;">Um convite (.ics) foi anexado a este e-mail para que você possa adicionar o evento à sua agenda.</p>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                    <table style="background: #f8fafc; border-top: 1px solid #e5e7eb; border-bottom: 1px solid #e5e7eb;" width="100%" cellspacing="0" cellpadding="0">
                        <tbody>
                            <tr>
                                <td style="padding-top: 25px; padding-right: 25px; padding-bottom: 25px; text-align: center;">
                                    <p style="margin: 0 0 5px 0; font-size: 18px; color: #111827; font-weight: 600;">Equipe MX2TECH</p>
                                    <p style="margin: 0; font-size: 14px; color: #6b7280;">Conte conosco para o que precisar</p>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                    <table style="background: #1f2937;" width="100%" cellspacing="0" cellpadding="0">
                        <tbody>
                            <tr>
                                <td style="padding: 30px 25px; text-align: center;">
                                    <h3 style="margin: 0 0 20px 0; font-size: 16px; color: #f9fafb; font-weight: 600;">Central de atendimento</h3>
                                    <p style="margin: 0 0 25px 0; font-size: 14px; color: #f9fafb;"><a style="color: #93c5fd; text-decoration: none;" href="tel:40426848">☎️ (85) 4042-6848</a> | <a style="color: #93c5fd; text-decoration: none;" href="https://wa.me/5585992136052">💬 (85) 99213-6052</a></p>
                                    <div style="margin: 0 0 25px 0;">
                                        <h3 style="margin: 0 0 15px 0; font-size: 16px; color: #f9fafb; font-weight: 600;">Nossas redes sociais</h3>
                                        <a href="https://www.instagram.com/mx2tech/"> <img src="https://img.icons8.com/color/48/000000/instagram-new.png" alt="Instagram" width="30"></a>
                                        <a href="https://www.linkedin.com/company/mx2tech/"> <img src="https://img.icons8.com/color/48/000000/linkedin.png" alt="LinkedIn" width="30"></a>
                                    </div>
                                </td>
                            </tr>
                            <tr>
                                <td style="padding: 15px; background: #111827; text-align: center;">
                                    <p style="margin: 0; font-size: 12px; color: #6b7280;">© {datetime.now().year} Mx2Tech Tecnologia. Todos os direitos reservados. <br><a style="color: #6b7280; text-decoration: underline;" href="https://www.mx2tech.com.br">www.mx2tech.com.br</a></p>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </td>
            </tr>
        </tbody>
    </table>
    """

    alt_part.attach(MIMEText(html, "html"))
    message_root.attach(alt_part)

    # Anexar logo (se existir)
    _attach_logo_to_message(message_root)

    # Anexar o arquivo .ics
    part = MIMEBase("text", "calendar", name="invite.ics")
    part.set_payload(ics_content)
    encoders.encode_base64(part)
    part.add_header("Content-Disposition", "attachment; filename=invite.ics")
    message_root.attach(part)

    # Enviar o e-mail
    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(smtp_server, smtp_port, context=context) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, to_emails, message_root.as_string())
        print(f"E-mail de confirmação enviado para {', '.join(to_emails)}")
        return True
    except Exception as e:
        print(f"Falha ao enviar e-mail: {e}")
        return False


def send_booking_update_notification(recipient_email, booking_details):
    """
    Envia um e-mail de notificação de atualização de agendamento.
    """
    smtp_settings = _get_smtp_settings()
    if not smtp_settings:
        return False
    sender_email, sender_password, smtp_server, smtp_port = smtp_settings

    message_root = MIMEMultipart("related")
    message_root["Subject"] = f"Atualização de Agendamento: {booking_details.get('summary', 'Agendamento de Sala')}"
    message_root["From"] = sender_email
    to_emails = [recipient_email, "ticket@mx2tech.com.br"]
    message_root["To"] = ", ".join(to_emails)

    alt_part = MIMEMultipart("alternative")

    plain_text = f"Atualização de Agendamento: {booking_details.get('summary')}\nInício: {booking_details.get('dtstart')}\nFim: {booking_details.get('dtend')}"
    alt_part.attach(MIMEText(plain_text, "plain"))

    html = f"""
    <table style="background: #f9f9f9; margin: 0 auto; max-width: 600px; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.1); font-family: 'Segoe UI', Arial, sans-serif;">
        <tbody>
            <tr>
                <td>
                    <table style="background-color: #ffc107;" width="100%" cellspacing="0" cellpadding="0">
                        <tbody>
                                        <tr>
                                            <td style="padding: 20px;" align="center"><img src="cid:logo" alt="image" width="80"></td>
                                        </tr>
                                        <tr>
                                            <td style="padding: 0 20px 30px 20px;" align="center">
                                                <h1 style="color: white; margin: 0; font-size: 24px; font-weight: 600;">Agendamento Atualizado!</h1>
                                            </td>
                                        </tr>                        </tbody>
                    </table>
                    <table style="background: #ffffff;" width="100%" cellspacing="0" cellpadding="0">
                        <tbody>
                            <tr>
                                <td style="padding: 30px 25px 10px 25px;">
                                    <p style="margin: 0 0 15px 0; font-size: 16px; color: #374151; line-height: 1.6;"><span style="font-weight: 600; color: #2563eb;">Olá, {booking_details.get('user_name', '')}!</span><br>Seu agendamento foi atualizado. Confira os novos detalhes:</p>
                                    <div style="background: #f3f4f6; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0; border-radius: 0 8px 8px 0;">
                                        <p style="margin: 0; font-size: 15px; color: #4b5563; line-height: 1.6;">
                                            <strong>Título: {booking_details.get('summary', '')}</strong><br>
                                            <strong>Sala:</strong> {booking_details.get('location', '')}<br>
                                            <strong>Início:</strong> {booking_details.get('dtstart').strftime('%d/%m/%Y %H:%M')}<br>
                                            <strong>Fim:</strong> {booking_details.get('dtend').strftime('%d/%m/%Y %H:%M')}<br>
                                            <strong>Descrição:</strong> {booking_details.get('description') or 'N/A'}
                                        </p>
                                    </div>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                    <!-- Footer -->
                </td>
            </tr>
        </tbody>
    </table>
    """

    alt_part.attach(MIMEText(html, "html"))
    message_root.attach(alt_part)

    _attach_logo_to_message(message_root)

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(smtp_server, smtp_port, context=context) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, to_emails, message_root.as_string())
        print(f"E-mail de atualização enviado para {', '.join(to_emails)}")
        return True
    except Exception as e:
        print(f"Falha ao enviar e-mail de atualização: {e}")
        return False


def send_booking_cancellation_notification(recipient_email, booking_details):
    """
    Envia um e-mail de notificação de cancelamento de agendamento.
    """
    smtp_settings = _get_smtp_settings()
    if not smtp_settings:
        return False
    sender_email, sender_password, smtp_server, smtp_port = smtp_settings

    message_root = MIMEMultipart("related")
    message_root["Subject"] = f"Cancelamento de Agendamento: {booking_details.get('summary', 'Agendamento de Sala')}"
    message_root["From"] = sender_email
    to_emails = [recipient_email, "ticket@mx2tech.com.br"]
    message_root["To"] = ", ".join(to_emails)

    alt_part = MIMEMultipart("alternative")

    plain_text = f"Cancelamento de Agendamento: {booking_details.get('summary')}\nInício: {booking_details.get('dtstart')}\nFim: {booking_details.get('dtend')}"
    alt_part.attach(MIMEText(plain_text, "plain"))

    html = f"""
    <table style="background: #f9f9f9; margin: 0 auto; max-width: 600px; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.1); font-family: 'Segoe UI', Arial, sans-serif;">
        <tbody>
            <tr>
                <td>
                    <table style="background-color: #dc3545;" width="100%" cellspacing="0" cellpadding="0">
                        <tbody>
                            <tr>
                                <td style="padding: 20px;" align="center"><img src="cid:logo" alt="image" width="80"></td>
                            </tr>
                            <tr>
                                <td style="padding: 0 20px 30px 20px;" align="center">
                                    <h1 style="color: white; margin: 0; font-size: 24px; font-weight: 600;">Agendamento Cancelado!</h1>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                    <table style="background: #ffffff;" width="100%" cellspacing="0" cellpadding="0">
                        <tbody>
                            <tr>
                                <td style="padding: 30px 25px 10px 25px;">
                                    <p style="margin: 0 0 15px 0; font-size: 16px; color: #374151; line-height: 1.6;"><span style="font-weight: 600; color: #2563eb;">Olá, {booking_details.get('user_name', '')}!</span><br>O agendamento abaixo foi cancelado:</p>
                                    <div style="background: #f3f4f6; border-left: 4px solid #dc3545; padding: 15px; margin: 20px 0; border-radius: 0 8px 8px 0;">
                                        <p style="margin: 0; font-size: 15px; color: #4b5563; line-height: 1.6;">
                                            <strong>Título: {booking_details.get('summary', '')}</strong><br>
                                            <strong>Sala:</strong> {booking_details.get('location', '')}<br>
                                            <strong>Início:</strong> {booking_details.get('dtstart').strftime('%d/%m/%Y %H:%M')}<br>
                                            <strong>Fim:</strong> {booking_details.get('dtend').strftime('%d/%m/%Y %H:%M')}
                                        </p>
                                    </div>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                    <!-- Footer -->
                </td>
            </tr>
        </tbody>
    </table>
    """

    alt_part.attach(MIMEText(html, "html"))
    message_root.attach(alt_part)

    _attach_logo_to_message(message_root)

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(smtp_server, smtp_port, context=context) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, to_emails, message_root.as_string())
        print(f"E-mail de cancelamento enviado para {', '.join(to_emails)}")
        return True
    except Exception as e:
        print(f"Falha ao enviar e-mail de cancelamento: {e}")
        return False
