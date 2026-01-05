"""
Configuration classes for SmartFridge application.

Supports development, testing, and production environments.
All sensitive values are loaded from environment variables.
"""

import os
from datetime import timedelta
from typing import Dict, Type


class Config:
    """Base configuration with defaults."""
    
    # Flask core
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI') or \
        'sqlite:///smartfridge.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
    }
    
    # Session security
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'false').lower() == 'true'
    SESSION_COOKIE_HTTPONLY = os.environ.get('SESSION_COOKIE_HTTPONLY', 'true').lower() == 'true'
    SESSION_COOKIE_SAMESITE = os.environ.get('SESSION_COOKIE_SAMESITE', 'Lax')
    PERMANENT_SESSION_LIFETIME = timedelta(hours=1)
    
    # CSRF protection
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600  # 1 hour
    
    # Flask-Talisman (security headers)
    TALISMAN_ENABLED = False
    FORCE_HTTPS = False
    CSP_POLICY = {
        'default-src': "'self'",
        'script-src': [
            "'self'",
            'cdn.jsdelivr.net',
            'cdnjs.cloudflare.com',
        ],
        'style-src': [
            "'self'",
            "'unsafe-inline'",
            'cdn.jsdelivr.net',
            'cdnjs.cloudflare.com',
        ],
        'font-src': [
            "'self'",
            'cdn.jsdelivr.net',
            'cdnjs.cloudflare.com',
        ],
        'img-src': "'self' data:",
        'frame-ancestors': "'none'",
    }
    
    # Rate limiting
    RATELIMIT_ENABLED = True
    RATELIMIT_STORAGE_URL = 'memory://'
    RATELIMIT_DEFAULT = '200 per day, 50 per hour'
    RATELIMIT_HEADERS_ENABLED = True
    
    # Mail configuration (optional)
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@smartfridge.local')
    
    # AI configuration
    AI_PROVIDER = os.environ.get('AI_PROVIDER', 'local')  # local, openai, azure
    AI_API_KEY = os.environ.get('AI_API_KEY')
    AI_MODEL = os.environ.get('AI_MODEL', 'gpt-3.5-turbo')
    AI_AZURE_ENDPOINT = os.environ.get('AI_AZURE_ENDPOINT')
    
    # Application settings
    ITEMS_PER_PAGE = 20
    EXPIRY_WARNING_DAYS = 3
    
    # Password policy
    PASSWORD_MIN_LENGTH = 8
    PASSWORD_REQUIRE_UPPERCASE = True
    PASSWORD_REQUIRE_LOWERCASE = True
    PASSWORD_REQUIRE_DIGIT = True
    PASSWORD_REQUIRE_SPECIAL = True
    BCRYPT_WORK_FACTOR = 12


class DevelopmentConfig(Config):
    """Development configuration."""
    
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI') or \
        'sqlite:///smartfridge_dev.db'
    
    # Disable rate limiting in development
    RATELIMIT_ENABLED = False
    
    # More verbose logging
    LOG_LEVEL = 'DEBUG'


class TestingConfig(Config):
    """Testing configuration."""
    
    TESTING = True
    DEBUG = True
    
    # Use in-memory SQLite for tests
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    
    # Disable CSRF for testing
    WTF_CSRF_ENABLED = False
    
    # Disable rate limiting for tests
    RATELIMIT_ENABLED = False
    
    # Faster password hashing for tests
    BCRYPT_WORK_FACTOR = 4
    
    # Fixed secret for reproducible tests
    SECRET_KEY = 'test-secret-key'
    
    # Disable login requirement message
    LOGIN_DISABLED = False


class ProductionConfig(Config):
    """Production configuration."""
    
    DEBUG = False
    TESTING = False
    
    # Force secure settings
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Enable security headers
    TALISMAN_ENABLED = True
    FORCE_HTTPS = True
    
    # Production database (PostgreSQL)
    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI') or \
        os.environ.get('DATABASE_URL')  # Azure uses DATABASE_URL
    
    # Fix for Heroku/Azure PostgreSQL URL format
    @property
    def SQLALCHEMY_DATABASE_URI(self):
        uri = os.environ.get('SQLALCHEMY_DATABASE_URI') or \
              os.environ.get('DATABASE_URL', '')
        # Handle postgres:// vs postgresql://
        if uri.startswith('postgres://'):
            uri = uri.replace('postgres://', 'postgresql://', 1)
        return uri
    
    # Production logging
    LOG_LEVEL = 'INFO'
    
    # Validate secret key is set
    @classmethod
    def init_app(cls, app):
        """Production-specific initialisation."""
        # Ensure secret key is set
        if app.config['SECRET_KEY'] == 'dev-secret-key-change-in-production':
            raise ValueError(
                'SECRET_KEY must be set to a secure value in production. '
                'Generate one with: python -c "import secrets; print(secrets.token_hex(32))"'
            )


config: Dict[str, Type[Config]] = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig,
}
