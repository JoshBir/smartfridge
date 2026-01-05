"""
SmartFridge CLI Commands

Provides management commands for database initialisation,
user management, and data seeding.
"""
import click
from flask import current_app
from flask.cli import with_appcontext

from app.extensions import db
from app.models.user import User
from app.models.recipe import Recipe
from app.services.security.password import PasswordService


@click.command('init-db')
@with_appcontext
def init_db_command():
    """Initialise the database with all tables."""
    db.create_all()
    click.echo('✓ Database initialised successfully.')


@click.command('create-admin')
@click.option('--username', prompt=True, help='Admin username')
@click.option('--email', prompt=True, help='Admin email address')
@click.option('--password', prompt=True, hide_input=True, 
              confirmation_prompt=True, help='Admin password')
@with_appcontext
def create_admin_command(username, email, password):
    """Create an admin user."""
    password_service = PasswordService()
    
    # Validate password
    is_valid, errors = password_service.validate_password(password)
    if not is_valid:
        click.echo('✗ Password validation failed:')
        for error in errors:
            click.echo(f'  - {error}')
        return
    
    # Check if user exists
    existing_user = User.query.filter(
        (User.username == username) | (User.email == email)
    ).first()
    
    if existing_user:
        click.echo('✗ A user with this username or email already exists.')
        return
    
    # Create admin user
    admin = User(
        username=username,
        email=email,
        password_hash=password_service.hash_password(password),
        role='admin',
        is_active=True,
        is_approved=True  # Admin users created via CLI are auto-approved
    )
    
    db.session.add(admin)
    db.session.commit()
    
    click.echo(f'✓ Admin user "{username}" created successfully.')


@click.command('set-password')
@click.option('--username', prompt=True, help='Username')
@click.option('--password', prompt=True, hide_input=True,
              confirmation_prompt=True, help='New password')
@with_appcontext
def set_password_command(username, password):
    """Set or reset a user's password."""
    password_service = PasswordService()
    
    # Validate password
    is_valid, errors = password_service.validate_password(password)
    if not is_valid:
        click.echo('✗ Password validation failed:')
        for error in errors:
            click.echo(f'  - {error}')
        return
    
    # Find user
    user = User.query.filter_by(username=username).first()
    if not user:
        click.echo(f'✗ User "{username}" not found.')
        return
    
    # Update password
    user.password_hash = password_service.hash_password(password)
    db.session.commit()
    
    click.echo(f'✓ Password updated for user "{username}".')


@click.command('seed-recipes')
@with_appcontext
def seed_recipes_command():
    """Load canonical recipes from JSON into the database as public recipes."""
    import json
    from pathlib import Path
    
    recipes_file = Path(current_app.root_path).parent / 'data' / 'canonical_recipes.json'
    
    if not recipes_file.exists():
        click.echo('✗ Canonical recipes file not found.')
        return
    
    with open(recipes_file, 'r', encoding='utf-8') as f:
        recipes_data = json.load(f)
    
    added_count = 0
    skipped_count = 0
    
    for recipe_data in recipes_data.get('recipes', []):
        # Check if recipe already exists (by title)
        existing = Recipe.query.filter_by(
            title=recipe_data['title'],
            user_id=None  # Public recipes have no user
        ).first()
        
        if existing:
            skipped_count += 1
            continue
        
        recipe = Recipe(
            title=recipe_data['title'],
            ingredients_text='\n'.join(f'• {ing}' for ing in recipe_data.get('ingredients', [])),
            instructions='\n'.join(f'{i+1}. {step}' for i, step in enumerate(recipe_data.get('instructions', []))),
            servings=recipe_data.get('servings'),
            prep_time_minutes=recipe_data.get('prep_time_minutes'),
            cook_time_minutes=recipe_data.get('cook_time_minutes'),
            is_ai_generated=False,
            user_id=None  # Public recipe
        )
        
        db.session.add(recipe)
        added_count += 1
    
    db.session.commit()
    
    click.echo(f'✓ Seeded {added_count} recipes ({skipped_count} already existed).')


@click.command('list-users')
@with_appcontext
def list_users_command():
    """List all users."""
    users = User.query.order_by(User.created_at.desc()).all()
    
    if not users:
        click.echo('No users found.')
        return
    
    click.echo(f'\n{"ID":<5} {"Username":<20} {"Email":<30} {"Role":<10} {"Active":<8}')
    click.echo('-' * 80)
    
    for user in users:
        active_status = '✓' if user.is_active else '✗'
        click.echo(f'{user.id:<5} {user.username:<20} {user.email:<30} {user.role:<10} {active_status:<8}')
    
    click.echo(f'\nTotal: {len(users)} user(s)')


@click.command('deactivate-user')
@click.option('--username', prompt=True, help='Username to deactivate')
@with_appcontext
def deactivate_user_command(username):
    """Deactivate a user account."""
    user = User.query.filter_by(username=username).first()
    
    if not user:
        click.echo(f'✗ User "{username}" not found.')
        return
    
    if not user.is_active:
        click.echo(f'User "{username}" is already deactivated.')
        return
    
    user.is_active = False
    db.session.commit()
    
    click.echo(f'✓ User "{username}" has been deactivated.')


@click.command('activate-user')
@click.option('--username', prompt=True, help='Username to activate')
@with_appcontext
def activate_user_command(username):
    """Activate a user account."""
    user = User.query.filter_by(username=username).first()
    
    if not user:
        click.echo(f'✗ User "{username}" not found.')
        return
    
    if user.is_active:
        click.echo(f'User "{username}" is already active.')
        return
    
    user.is_active = True
    db.session.commit()
    
    click.echo(f'✓ User "{username}" has been activated.')


@click.command('clean-expired')
@click.option('--days', default=30, help='Remove items expired for more than N days')
@click.option('--dry-run', is_flag=True, help='Show what would be deleted without deleting')
@with_appcontext
def clean_expired_command(days, dry_run):
    """Remove items that have been expired for a specified number of days."""
    from datetime import datetime, timedelta
    from app.models.item import Item
    
    cutoff_date = datetime.utcnow().date() - timedelta(days=days)
    
    expired_items = Item.query.filter(Item.expiry_date < cutoff_date).all()
    
    if not expired_items:
        click.echo(f'No items expired for more than {days} days.')
        return
    
    click.echo(f'Found {len(expired_items)} item(s) expired for more than {days} days:')
    
    for item in expired_items:
        days_expired = (datetime.utcnow().date() - item.expiry_date).days
        click.echo(f'  - {item.name} (expired {days_expired} days ago, user: {item.owner.username})')
    
    if dry_run:
        click.echo('\n[Dry run - no items deleted]')
    else:
        for item in expired_items:
            db.session.delete(item)
        db.session.commit()
        click.echo(f'\n✓ Deleted {len(expired_items)} expired item(s).')


def register_cli_commands(app):
    """Register all CLI commands with the Flask app."""
    app.cli.add_command(init_db_command)
    app.cli.add_command(create_admin_command)
    app.cli.add_command(set_password_command)
    app.cli.add_command(seed_recipes_command)
    app.cli.add_command(list_users_command)
    app.cli.add_command(deactivate_user_command)
    app.cli.add_command(activate_user_command)
    app.cli.add_command(clean_expired_command)
