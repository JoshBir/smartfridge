"""
Flask extensions initialisation.

Extensions are initialised without an app instance and bound later
via the application factory pattern.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate
from flask_talisman import Talisman
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address


# Database ORM
db = SQLAlchemy()

# User session management
login_manager = LoginManager()

# CSRF protection
csrf = CSRFProtect()

# Database migrations
migrate = Migrate()

# Security headers
talisman = Talisman()

# Rate limiting
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",
)
