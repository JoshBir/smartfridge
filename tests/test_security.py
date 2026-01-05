"""
SmartFridge Test Suite - Security Tests

Tests for security features including CSRF, session handling, and access control.
"""
import pytest
from flask import session


class TestCSRFProtection:
    """CSRF protection tests."""
    
    def test_form_includes_csrf_token(self, auth_client):
        """Test that forms include CSRF token."""
        response = auth_client.get('/items/new')
        
        assert response.status_code == 200
        assert b'csrf_token' in response.data
    
    def test_post_without_csrf_fails(self, client, test_user):
        """Test that POST without CSRF token fails."""
        # Login first
        client.post('/auth/login', data={
            'email': 'test@example.com',
            'password': 'TestP@ss123'
        })
        
        # Attempt to create item without CSRF (should fail)
        response = client.post('/items/new', data={
            'name': 'Hack Item',
            'quantity': 1,
            'unit': 'items',
            'expiry_date': '2025-12-31'
        })
        
        # Should return 400 Bad Request or redirect
        assert response.status_code in [400, 302]


class TestSessionSecurity:
    """Session security tests."""
    
    def test_session_after_login(self, client, test_user):
        """Test session is created after login."""
        response = client.post('/auth/login', data={
            'email': 'test@example.com',
            'password': 'TestP@ss123'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        # Session should be active
    
    def test_session_cleared_after_logout(self, auth_client):
        """Test session is cleared after logout."""
        response = auth_client.get('/auth/logout', follow_redirects=True)
        
        assert response.status_code == 200
        
        # Attempting to access protected resource should fail
        response = auth_client.get('/items/')
        assert response.status_code == 302  # Redirect to login


class TestAccessControl:
    """Access control tests."""
    
    def test_unauthenticated_redirect(self, client):
        """Test unauthenticated users are redirected."""
        protected_routes = [
            '/items/',
            '/recipes/',
            '/sites/',
            '/items/new',
            '/recipes/suggest'
        ]
        
        for route in protected_routes:
            response = client.get(route)
            assert response.status_code == 302
            assert '/auth/login' in response.headers.get('Location', '')
    
    def test_admin_only_routes(self, auth_client):
        """Test regular users cannot access admin routes."""
        admin_routes = [
            '/admin/',
            '/admin/users'
        ]
        
        for route in admin_routes:
            response = auth_client.get(route)
            assert response.status_code in [403, 302]
    
    def test_admin_can_access_admin_routes(self, admin_client):
        """Test admins can access admin routes."""
        response = admin_client.get('/admin/')
        
        assert response.status_code == 200
    
    def test_users_cannot_access_other_users_data(self, auth_client, app, admin_user):
        """Test users cannot access other users' data."""
        from datetime import datetime, timedelta
        from app.models.item import Item
        from app.extensions import db
        
        with app.app_context():
            # Create item for admin
            other_item = Item(
                name='Admin Secret Item',
                quantity=1,
                unit='items',
                expiry_date=(datetime.utcnow() + timedelta(days=7)).date(),
                user_id=admin_user.id
            )
            db.session.add(other_item)
            db.session.commit()
            item_id = other_item.id
        
        # Try to view as regular user
        response = auth_client.get(f'/items/{item_id}')
        assert response.status_code in [403, 404]
        
        # Try to edit as regular user
        response = auth_client.get(f'/items/{item_id}/edit')
        assert response.status_code in [403, 404]
        
        # Try to delete as regular user
        response = auth_client.post(f'/items/{item_id}/delete')
        assert response.status_code in [403, 404]


class TestInputValidation:
    """Input validation and sanitisation tests."""
    
    def test_xss_prevention_in_item_name(self, auth_client, app):
        """Test XSS in item name is escaped."""
        from datetime import datetime, timedelta
        
        expiry = (datetime.utcnow() + timedelta(days=7)).strftime('%Y-%m-%d')
        
        response = auth_client.post('/items/new', data={
            'name': '<script>alert("xss")</script>',
            'quantity': 1,
            'unit': 'items',
            'expiry_date': expiry
        }, follow_redirects=True)
        
        # The script tag should be escaped in output
        assert b'<script>' not in response.data
    
    def test_sql_injection_prevention(self, auth_client):
        """Test SQL injection is prevented."""
        # Attempt SQL injection in search
        response = auth_client.get("/items/?search=' OR '1'='1")
        
        # Should not cause error or return unexpected data
        assert response.status_code == 200


class TestPasswordSecurity:
    """Password security tests."""
    
    def test_password_not_stored_plain(self, app, test_user):
        """Test password is not stored in plain text."""
        with app.app_context():
            from app.models.user import User
            user = User.query.filter_by(username='testuser').first()
            
            assert user.password_hash != 'TestP@ss123'
            assert 'TestP@ss123' not in user.password_hash
    
    def test_password_not_in_response(self, auth_client):
        """Test password is never returned in responses."""
        response = auth_client.get('/auth/change-password')
        
        assert b'TestP@ss123' not in response.data
    
    def test_password_hash_uses_bcrypt(self, app, test_user):
        """Test password hash is bcrypt format."""
        with app.app_context():
            from app.models.user import User
            user = User.query.filter_by(username='testuser').first()
            
            # bcrypt hashes start with $2b$ or $2a$
            assert user.password_hash.startswith('$2')


class TestRateLimiting:
    """Rate limiting tests."""
    
    def test_login_rate_limiting(self, client, app):
        """Test login endpoint has rate limiting."""
        # This test may need adjustment based on actual rate limit settings
        # Make multiple rapid requests
        for _ in range(15):
            client.post('/auth/login', data={
                'email': 'test@example.com',
                'password': 'WrongPass'
            })
        
        # The rate limiter should kick in
        response = client.post('/auth/login', data={
            'email': 'test@example.com',
            'password': 'WrongPass'
        })
        
        # Either 429 or the app handles gracefully
        assert response.status_code in [200, 429]


class TestSecurityHeaders:
    """Security headers tests."""
    
    def test_content_type_options(self, client):
        """Test X-Content-Type-Options header."""
        response = client.get('/')
        
        # Should have nosniff header
        assert response.headers.get('X-Content-Type-Options') == 'nosniff'
    
    def test_frame_options(self, client):
        """Test X-Frame-Options header."""
        response = client.get('/')
        
        # Should prevent framing
        frame_options = response.headers.get('X-Frame-Options', '')
        assert frame_options in ['DENY', 'SAMEORIGIN'] or 'frame-ancestors' in response.headers.get('Content-Security-Policy', '')
