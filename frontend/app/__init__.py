from flask import Flask
from flask_ldap3_login import LDAP3LoginManager
from flask_login import LoginManager
import os
import redis
from datetime import timedelta

ldap_manager = LDAP3LoginManager()
login_manager = LoginManager()


def get_redis_connection(app):
    return redis.Redis(
        host=app.config['REDIS_HOST'],
        port=app.config['REDIS_PORT'],
        db=app.config['REDIS_DB']
    )


def create_app():
    app = Flask(__name__)

    # Load config
    app.config.from_pyfile('config.py')

    # Initialize extensions
    ldap_manager.init_app(app)
    login_manager.init_app(app)

    # Register blueprints
    from frontend.app.auth.routes import auth_bp
    from frontend.app.admin.routes import admin_bp
    from frontend.app.tokens.routes import tokens_bp
    from frontend.app.main.routes import main_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(tokens_bp)

    # Ensure data directory exists
    os.makedirs(app.config['DATA_DIR'], exist_ok=True)

    # Initialize filters
    from .filters import init_app as init_filters
    init_filters(app)

    # Configure session to use Redis
    app.config['SESSION_TYPE'] = 'redis'
    app.config['SESSION_REDIS'] = get_redis_connection(app)
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=1)

    return app
