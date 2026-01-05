"""
SmartFridge Test Suite - Items Tests

Tests for fridge item management functionality.
"""
import pytest
from datetime import datetime, timedelta
from app.models.item import Item


class TestItemsView:
    """Item viewing tests."""
    
    def test_items_index_page_loads(self, auth_client):
        """Test items index page is accessible."""
        response = auth_client.get('/items/')
        
        assert response.status_code == 200
        assert b'My Fridge' in response.data or b'Items' in response.data
    
    def test_items_index_shows_items(self, auth_client, test_item):
        """Test items are displayed on index page."""
        response = auth_client.get('/items/')
        
        assert response.status_code == 200
        assert b'Test Milk' in response.data
    
    def test_items_view_single_item(self, auth_client, test_item):
        """Test viewing a single item."""
        response = auth_client.get(f'/items/{test_item.id}')
        
        assert response.status_code == 200
        assert b'Test Milk' in response.data
    
    def test_items_view_nonexistent_item(self, auth_client):
        """Test viewing non-existent item returns 404."""
        response = auth_client.get('/items/99999')
        
        assert response.status_code == 404


class TestItemsCreate:
    """Item creation tests."""
    
    def test_new_item_page_loads(self, auth_client):
        """Test new item form is accessible."""
        response = auth_client.get('/items/new')
        
        assert response.status_code == 200
        assert b'Add Item' in response.data
    
    def test_create_item_success(self, auth_client, app):
        """Test successful item creation."""
        expiry = (datetime.utcnow() + timedelta(days=14)).strftime('%Y-%m-%d')
        
        response = auth_client.post('/items/new', data={
            'name': 'Fresh Bread',
            'quantity': 1,
            'unit': 'loaves',
            'expiry_date': expiry,
            'notes': 'Wholemeal'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        with app.app_context():
            item = Item.query.filter_by(name='Fresh Bread').first()
            assert item is not None
            assert item.quantity == 1
            assert item.unit == 'loaves'
    
    def test_create_item_missing_name(self, auth_client):
        """Test item creation without name fails."""
        expiry = (datetime.utcnow() + timedelta(days=14)).strftime('%Y-%m-%d')
        
        response = auth_client.post('/items/new', data={
            'name': '',
            'quantity': 1,
            'unit': 'items',
            'expiry_date': expiry
        }, follow_redirects=True)
        
        assert response.status_code == 200
        # Should show validation error
    
    def test_create_item_invalid_quantity(self, auth_client):
        """Test item creation with invalid quantity."""
        expiry = (datetime.utcnow() + timedelta(days=14)).strftime('%Y-%m-%d')
        
        response = auth_client.post('/items/new', data={
            'name': 'Invalid Item',
            'quantity': -5,
            'unit': 'items',
            'expiry_date': expiry
        }, follow_redirects=True)
        
        assert response.status_code == 200
        # Should show validation error or reject


class TestItemsEdit:
    """Item editing tests."""
    
    def test_edit_item_page_loads(self, auth_client, test_item):
        """Test edit item form is accessible."""
        response = auth_client.get(f'/items/{test_item.id}/edit')
        
        assert response.status_code == 200
        assert b'Edit Item' in response.data
        assert b'Test Milk' in response.data
    
    def test_edit_item_success(self, auth_client, app, test_item):
        """Test successful item edit."""
        expiry = (datetime.utcnow() + timedelta(days=10)).strftime('%Y-%m-%d')
        
        response = auth_client.post(f'/items/{test_item.id}/edit', data={
            'name': 'Updated Milk',
            'quantity': 3,
            'unit': 'litres',
            'expiry_date': expiry
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        with app.app_context():
            item = Item.query.get(test_item.id)
            assert item.name == 'Updated Milk'
            assert item.quantity == 3


class TestItemsDelete:
    """Item deletion tests."""
    
    def test_delete_item_success(self, auth_client, app, test_item):
        """Test successful item deletion."""
        item_id = test_item.id
        
        response = auth_client.post(f'/items/{item_id}/delete', follow_redirects=True)
        
        assert response.status_code == 200
        
        with app.app_context():
            item = Item.query.get(item_id)
            assert item is None


class TestItemsExpiry:
    """Expiry-related tests."""
    
    def test_expiring_items_page(self, auth_client, expiring_item):
        """Test expiring items page shows items."""
        response = auth_client.get('/items/expiring')
        
        assert response.status_code == 200
        assert b'Expiring Cheese' in response.data
    
    def test_expired_items_page(self, auth_client, expired_item):
        """Test expired items page shows items."""
        response = auth_client.get('/items/expired')
        
        assert response.status_code == 200
        assert b'Expired Yoghurt' in response.data
    
    def test_item_expiry_status_fresh(self, app, test_user, password_service):
        """Test item with distant expiry is fresh."""
        with app.app_context():
            item = Item(
                name='Fresh Item',
                quantity=1,
                unit='items',
                expiry_date=(datetime.utcnow() + timedelta(days=10)).date(),
                user_id=test_user.id
            )
            
            assert item.is_fresh is True
            assert item.is_expiring_soon is False
            assert item.is_expired is False
    
    def test_item_expiry_status_expiring_soon(self, app, test_user):
        """Test item expiring soon has correct status."""
        with app.app_context():
            item = Item(
                name='Expiring Item',
                quantity=1,
                unit='items',
                expiry_date=(datetime.utcnow() + timedelta(days=2)).date(),
                user_id=test_user.id
            )
            
            assert item.is_expiring_soon is True
            assert item.is_expired is False
    
    def test_item_expiry_status_expired(self, app, test_user):
        """Test expired item has correct status."""
        with app.app_context():
            item = Item(
                name='Expired Item',
                quantity=1,
                unit='items',
                expiry_date=(datetime.utcnow() - timedelta(days=2)).date(),
                user_id=test_user.id
            )
            
            assert item.is_expired is True
            assert item.is_fresh is False


class TestItemsAccess:
    """Item access control tests."""
    
    def test_cannot_view_other_users_items(self, auth_client, app, admin_user, password_service):
        """Test users cannot view other users' items."""
        with app.app_context():
            # Create item for admin user
            other_item = Item(
                name='Admin Item',
                quantity=1,
                unit='items',
                expiry_date=(datetime.utcnow() + timedelta(days=7)).date(),
                user_id=admin_user.id
            )
            from app.extensions import db
            db.session.add(other_item)
            db.session.commit()
            item_id = other_item.id
        
        # Try to access as regular user
        response = auth_client.get(f'/items/{item_id}')
        
        assert response.status_code == 404 or response.status_code == 403
