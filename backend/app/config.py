import os


def _split_csv_env(value: str, default: str) -> list[str]:
    raw = value if value is not None else default
    return [item.strip() for item in raw.split(',') if item.strip()]


def _bool_env(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {'1', 'true', 'yes', 'on'}


class Config:
    """Application configuration loaded from environment."""

    SECRET_KEY = os.environ.get('SECRET_KEY')

    DB_USER = os.environ.get('DB_USER')
    DB_PASSWORD = os.environ.get('DB_PASSWORD')
    DB_DSN = os.environ.get('DB_DSN')

    # Oracle session pool settings
    DB_POOL_MIN = int(os.environ.get('DB_POOL_MIN', '2'))
    DB_POOL_MAX = int(os.environ.get('DB_POOL_MAX', '20'))
    DB_POOL_INCREMENT = int(os.environ.get('DB_POOL_INCREMENT', '2'))

    # JWT
    JWT_EXP_HOURS = int(os.environ.get('JWT_EXP_HOURS', '24'))

    # Password security and migration
    ALLOW_LEGACY_PASSWORD = _bool_env(os.environ.get('ALLOW_LEGACY_PASSWORD'), True)
    PASSWORD_MIGRATE_ON_LOGIN = _bool_env(os.environ.get('PASSWORD_MIGRATE_ON_LOGIN'), True)
    PASSWORD_HASH_ROUNDS = int(os.environ.get('PASSWORD_HASH_ROUNDS', '12'))
    PASSWORD_HASH_COLUMN = os.environ.get('PASSWORD_HASH_COLUMN', 'SENHA_HASH')

    # Login brute-force protection
    LOGIN_MAX_ATTEMPTS = int(os.environ.get('LOGIN_MAX_ATTEMPTS', '5'))
    LOGIN_WINDOW_SECONDS = int(os.environ.get('LOGIN_WINDOW_SECONDS', '600'))
    LOGIN_BLOCK_SECONDS = int(os.environ.get('LOGIN_BLOCK_SECONDS', '900'))

    # CORS
    CORS_ORIGINS = _split_csv_env(
        os.environ.get('CORS_ORIGINS'),
        'http://localhost:8002,http://127.0.0.1:8002',
    )

    # SMTP (must come from environment)
    SMTP_SERVER = os.environ.get('SMTP_SERVER')
    SMTP_PORT = int(os.environ.get('SMTP_PORT', '465'))
    SMTP_USER = os.environ.get('SMTP_USER')
    SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD')
