"""
Main blueprint for SmartFridge application.

Handles the dashboard and home page.
"""

from flask import Blueprint, render_template
from flask_login import login_required, current_user

from app.models.item import Item
from app.models.recipe import Recipe
from app.models.site import Site


main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """Landing page - redirects to dashboard if logged in."""
    if current_user.is_authenticated:
        return dashboard()
    return render_template('main/index.html')


@main_bp.route('/dashboard')
@login_required
def dashboard():
    """User dashboard with overview of items, recipes, and sites."""
    # Get item statistics
    items = Item.get_by_owner(current_user.id)
    expiring_items = Item.get_expiring_soon(current_user.id, days=3)
    expired_items = Item.get_expired(current_user.id)
    
    # Get counts
    total_items = len(items)
    total_recipes = Recipe.query.filter_by(owner_id=current_user.id).count()
    total_sites = Site.query.filter_by(owner_id=current_user.id).count()
    
    # Category breakdown
    categories = {}
    for item in items:
        cat = item.category.replace('_', ' ').title()
        categories[cat] = categories.get(cat, 0) + 1
    
    return render_template(
        'main/dashboard.html',
        total_items=total_items,
        total_recipes=total_recipes,
        total_sites=total_sites,
        expiring_items=expiring_items,
        expired_items=expired_items,
        categories=categories,
    )


@main_bp.route('/about')
def about():
    """About page."""
    return render_template('main/about.html')
