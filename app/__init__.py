"""
SmartFridge Application Factory.

A secure, production-ready Flask application for managing fridge ingredients,
generating AI recipe suggestions, and organising favourite cooking websites.
"""

import os
import logging
from typing import Optional

from flask import Flask, render_template
from werkzeug.middleware.proxy_fix import ProxyFix

from app.config import config
from app.extensions import db, login_manager, csrf, migrate, talisman, limiter


def create_app(config_name: Optional[str] = None) -> Flask:
    """
    Application factory for SmartFridge.
    
    Args:
        config_name: Configuration environment name (development, testing, production).
                     Defaults to FLASK_CONFIG environment variable or 'development'.
    
    Returns:
        Configured Flask application instance.
    """
    if config_name is None:
        config_name = os.environ.get('FLASK_CONFIG', 'development')
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Configure logging
    configure_logging(app)
    
    # Handle proxy headers in production (for Azure App Service, Nginx)
    if config_name == 'production':
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
    
    # Initialise extensions
    initialise_extensions(app)
    
    # Register blueprints
    register_blueprints(app)
    
    # Register CLI commands
    register_cli_commands(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register context processors
    register_context_processors(app)
    
    return app


def configure_logging(app: Flask) -> None:
    """Configure application logging."""
    log_level = logging.DEBUG if app.debug else logging.INFO
    
    handler = logging.StreamHandler()
    handler.setLevel(log_level)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    
    app.logger.addHandler(handler)
    app.logger.setLevel(log_level)


def initialise_extensions(app: Flask) -> None:
    """Initialise Flask extensions."""
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    migrate.init_app(app, db)
    limiter.init_app(app)
    
    # Configure Talisman for security headers (only in production)
    if app.config.get('TALISMAN_ENABLED', False):
        talisman.init_app(
            app,
            content_security_policy=app.config.get('CSP_POLICY'),
            force_https=app.config.get('FORCE_HTTPS', True),
            frame_options='DENY',
            referrer_policy='strict-origin-when-cross-origin',
            session_cookie_secure=app.config.get('SESSION_COOKIE_SECURE', True),
            session_cookie_http_only=True,
        )
    
    # Configure login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id: str):
        from app.models.user import User
        return User.query.get(int(user_id))


def register_blueprints(app: Flask) -> None:
    """Register application blueprints."""
    from app.blueprints.main import main_bp
    from app.blueprints.auth import auth_bp
    from app.blueprints.items import items_bp
    from app.blueprints.recipes import recipes_bp
    from app.blueprints.sites import sites_bp
    from app.blueprints.admin import admin_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(items_bp, url_prefix='/items')
    app.register_blueprint(recipes_bp, url_prefix='/recipes')
    app.register_blueprint(sites_bp, url_prefix='/sites')
    app.register_blueprint(admin_bp, url_prefix='/admin')


def register_cli_commands(app: Flask) -> None:
    """Register Flask CLI commands."""
    from app.cli import register_cli_commands as register_commands
    register_commands(app)


def register_error_handlers(app: Flask) -> None:
    """Register error handlers."""
    
    @app.errorhandler(400)
    def bad_request(error):
        return render_template('errors/400.html'), 400
    
    @app.errorhandler(403)
    def forbidden(error):
        return render_template('errors/403.html'), 403
    
    @app.errorhandler(404)
    def not_found(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500


def register_context_processors(app: Flask) -> None:
    """Register template context processors."""
    
    @app.context_processor
    def inject_globals():
        from datetime import datetime, timedelta
        return {
            'now': datetime.utcnow(),
            'expiry_warning_days': 3,
            'timedelta': timedelta,
        }
