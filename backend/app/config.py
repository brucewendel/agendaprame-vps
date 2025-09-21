import os

class Config:
    """Classe de configuração base."""
    SECRET_KEY = os.environ.get('SECRET_KEY')
    DB_USER = os.environ.get('DB_USER')
    DB_PASSWORD = os.environ.get('DB_PASSWORD')
    DB_DSN = os.environ.get('DB_DSN')