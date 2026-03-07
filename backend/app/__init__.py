from flask import Flask
from flask_cors import CORS


def create_app():
    """Create and configure the Flask app instance."""
    app = Flask(__name__)
    app.config.from_object('app.config.Config')

    if not app.config.get('SECRET_KEY'):
        raise RuntimeError('SECRET_KEY is required in environment variables.')

    cors_origins = app.config.get('CORS_ORIGINS', [])
    CORS(
        app,
        resources={r"/*": {"origins": cors_origins}},
        supports_credentials=False,
    )

    from .routes import main as main_blueprint
    app.register_blueprint(main_blueprint)

    return app
