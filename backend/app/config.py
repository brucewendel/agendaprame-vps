import os

class Config:
    """Classe de configuração base."""
    SECRET_KEY = os.environ.get('SECRET_KEY')
    DB_USER = os.environ.get('DB_USER')
    DB_PASSWORD = os.environ.get('DB_PASSWORD')
    DB_DSN = os.environ.get('DB_DSN')

    # Configurações de E-mail SMTP
    SMTP_SERVER = "ns20.mx2tech.cloud"
    SMTP_PORT = 465
    SMTP_USER = "stvm2@jadistribuidora.net"
    SMTP_PASSWORD = "jad#3216@"
