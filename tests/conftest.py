"""
SmartFridge Test Suite - Fixtures

Shared pytest fixtures for all tests.
"""
import pytest
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.item import Item
from app.models.recipe import Recipe
from app.models.site import Site
from app.services.security.password import PasswordService


@pytest.fixture(scope='session')
def app():
    """Create application for the test session."""
    app = create_app('testing')
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    """Create a test client for each test."""
    with app.test_client() as client:
        with app.app_context():
            yield client


@pytest.fixture
def runner(app):
    """Create a CLI test runner."""
    return app.test_cli_runner()


@pytest.fixture
def password_service():
    """Provide a password service instance."""
    return PasswordService()


@pytest.fixture
def test_user(app, password_service):
    """Create a standard test user."""
    with app.app_context():
        user = User.query.filter_by(username='testuser').first()
        if not user:
            user = User(
                username='testuser',
                email='test@example.com',
                password_hash=password_service.hash_password('TestP@ss123'),
                role='user',
                is_active=True
            )
            db.session.add(user)
            db.session.commit()
        yield user
        # Cleanup after test
        User.query.filter_by(username='testuser').delete()
        db.session.commit()


@pytest.fixture
def admin_user(app, password_service):
    """Create an admin test user."""
    with app.app_context():
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@example.com',
                password_hash=password_service.hash_password('AdminP@ss123'),
                role='admin',
                is_active=True
            )
            db.session.add(admin)
            db.session.commit()
        yield admin
        User.query.filter_by(username='admin').delete()
        db.session.commit()


@pytest.fixture
def inactive_user(app, password_service):
    """Create an inactive test user."""
    with app.app_context():
        user = User.query.filter_by(username='inactiveuser').first()
        if not user:
            user = User(
                username='inactiveuser',
                email='inactive@example.com',
                password_hash=password_service.hash_password('TestP@ss123'),
                role='user',
                is_active=False
            )
            db.session.add(user)
            db.session.commit()
        yield user
        User.query.filter_by(username='inactiveuser').delete()
        db.session.commit()


@pytest.fixture
def auth_client(client, test_user):
    """Create an authenticated test client."""
    client.post('/auth/login', data={
        'email': 'test@example.com',
        'password': 'TestP@ss123'
    })
    yield client


@pytest.fixture
def admin_client(client, admin_user):
    """Create an authenticated admin client."""
    client.post('/auth/login', data={
        'email': 'admin@example.com',
        'password': 'AdminP@ss123'
    })
    yield client


@pytest.fixture
def test_item(app, test_user):
    """Create a test item."""
    from datetime import datetime, timedelta
    
    with app.app_context():
        item = Item(
            name='Test Milk',
            quantity=2,
            unit='litres',
            expiry_date=(datetime.utcnow() + timedelta(days=7)).date(),
            user_id=test_user.id
        )
        db.session.add(item)
        db.session.commit()
        yield item
        Item.query.filter_by(id=item.id).delete()
        db.session.commit()


@pytest.fixture
def expired_item(app, test_user):
    """Create an expired test item."""
    from datetime import datetime, timedelta
    
    with app.app_context():
        item = Item(
            name='Expired Yoghurt',
            quantity=1,
            unit='pots',
            expiry_date=(datetime.utcnow() - timedelta(days=3)).date(),
            user_id=test_user.id
        )
        db.session.add(item)
        db.session.commit()
        yield item
        Item.query.filter_by(id=item.id).delete()
        db.session.commit()


@pytest.fixture
def expiring_item(app, test_user):
    """Create an item expiring soon."""
    from datetime import datetime, timedelta
    
    with app.app_context():
        item = Item(
            name='Expiring Cheese',
            quantity=1,
            unit='blocks',
            expiry_date=(datetime.utcnow() + timedelta(days=2)).date(),
            user_id=test_user.id
        )
        db.session.add(item)
        db.session.commit()
        yield item
        Item.query.filter_by(id=item.id).delete()
        db.session.commit()


@pytest.fixture
def test_recipe(app, test_user):
    """Create a test recipe."""
    with app.app_context():
        recipe = Recipe(
            title='Test Omelette',
            ingredients_text='• 3 eggs\n• Salt and pepper\n• Butter',
            instructions='1. Beat eggs\n2. Cook in butter\n3. Season and serve',
            servings=2,
            prep_time_minutes=5,
            cook_time_minutes=10,
            user_id=test_user.id
        )
        db.session.add(recipe)
        db.session.commit()
        yield recipe
        Recipe.query.filter_by(id=recipe.id).delete()
        db.session.commit()


@pytest.fixture
def test_site(app, test_user):
    """Create a test site."""
    with app.app_context():
        site = Site(
            name='Test Cooking Site',
            url='https://example-cooking.com',
            description='A test cooking website',
            tags='testing, example',
            user_id=test_user.id
        )
        db.session.add(site)
        db.session.commit()
        yield site
        Site.query.filter_by(id=site.id).delete()
        db.session.commit()
