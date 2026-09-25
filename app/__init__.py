from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from app.config import Config
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(get_remote_address, default_limits=["10 per minute"])
db = SQLAlchemy()
jwt = JWTManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    jwt.init_app(app)
    limiter.init_app(app)
    CORS(app)

    with app.app_context():
        from app.models import User, Player, Match, ChatMessage
        db.create_all()

    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.player import player_bp
    from app.routes.chat import chat_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(player_bp, url_prefix='/api/player')
    app.register_blueprint(chat_bp, url_prefix='/api/chat')
    
    @app.route("/")
    def greeting():
        return "Welcome to the gaming coach api\n"
    
    @app.route("/api/health")
    def health():
        db.session.execute(text("SELECT 1"))
        return jsonify({"status": "ok", "database": "connected"})

    return app