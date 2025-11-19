import os

class Config:
    """Classe de configuração base."""
    SECRET_KEY = os.environ.get('SECRET_KEY')
    DB_USER = os.environ.get('DB_USER')
    DB_PASSWORD = os.environ.get('DB_PASSWORD')
    DB_DSN = os.environ.get('DB_DSN')

    # Configurações de E-mail SMTP
    SMTP_SERVER = "ns50.meuemailmx.com.br"
    SMTP_PORT = 465
    SMTP_USER = "suporte@jadistribuidora.net"
    SMTP_PASSWORD = "Jad@20172018"
