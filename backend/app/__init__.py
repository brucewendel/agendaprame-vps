import os
from pathlib import Path

from flask import Flask, abort, send_from_directory
from flask_cors import CORS


def _frontend_dir() -> str:
    configured_dir = os.environ.get('FRONTEND_DIR')
    if configured_dir:
        return configured_dir

    project_root = Path(__file__).resolve().parents[2]
    return str(project_root / 'frontend')


def create_app():
    """Create and configure the Flask app instance."""
    frontend_dir = _frontend_dir()
    app = Flask(__name__, static_folder=frontend_dir, static_url_path='')
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
    app.register_blueprint(main_blueprint, url_prefix='/api', name='api')

    @app.route('/')
    def serve_index():
        return send_from_directory(frontend_dir, 'index.html')

    @app.route('/<path:path>')
    def serve_frontend(path):
        if path == 'api' or path.startswith('api/'):
            abort(404)

        requested_file = Path(frontend_dir) / path
        if requested_file.is_file():
            return send_from_directory(frontend_dir, path)
        return send_from_directory(frontend_dir, 'index.html')

    return app
