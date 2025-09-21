from flask import Flask
from flask_cors import CORS

def create_app():
    """Cria e configura a instância da aplicação Flask."""
    app = Flask(__name__)
    CORS(app, resources={r"/*": {"origins": "*"}})
    app.config.from_object('app.config.Config')

    # Importa e registra os blueprints (rotas)
    from .routes import main as main_blueprint
    app.register_blueprint(main_blueprint)

    return app
