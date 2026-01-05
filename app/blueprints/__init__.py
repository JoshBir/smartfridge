"""
Blueprints package.
"""

from app.blueprints.main import main_bp
from app.blueprints.auth import auth_bp
from app.blueprints.items import items_bp
from app.blueprints.recipes import recipes_bp
from app.blueprints.sites import sites_bp
from app.blueprints.admin import admin_bp

__all__ = [
    'main_bp',
    'auth_bp',
    'items_bp',
    'recipes_bp',
    'sites_bp',
    'admin_bp',
]
