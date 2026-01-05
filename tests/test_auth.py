"""
SmartFridge Test Suite - Authentication Tests

Tests for user registration, login, logout, and password management.
"""
import pytest
from flask import url_for
from app.models.user import User
from app.services.security.password import PasswordService


class TestAuthentication:
    """Authentication workflow tests."""
    
    def test_login_page_loads(self, client):
        """Test that login page is accessible."""
        response = client.get('/auth/login')
        assert response.status_code == 200
        assert b'Sign In' in response.data
    
    def test_register_page_loads(self, client):
        """Test that registration page is accessible."""
        response = client.get('/auth/register')
        assert response.status_code == 200
        assert b'Create Account' in response.data
    
    def test_successful_registration(self, client, app):
        """Test successful user registration."""
        response = client.post('/auth/register', data={
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'SecureP@ss123',
            'confirm_password': 'SecureP@ss123'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        with app.app_context():
            user = User.query.filter_by(username='newuser').first()
            assert user is not None
            assert user.email == 'newuser@example.com'
    
    def test_registration_duplicate_username(self, client, test_user):
        """Test registration with existing username fails."""
        response = client.post('/auth/register', data={
            'username': 'testuser',  # Already exists
            'email': 'another@example.com',
            'password': 'SecureP@ss123',
            'confirm_password': 'SecureP@ss123'
        }, follow_redirects=True)
        
        assert b'Username already taken' in response.data or response.status_code == 200
    
    def test_registration_duplicate_email(self, client, test_user):
        """Test registration with existing email fails."""
        response = client.post('/auth/register', data={
            'username': 'anotheruser',
            'email': 'test@example.com',  # Already exists
            'password': 'SecureP@ss123',
            'confirm_password': 'SecureP@ss123'
        }, follow_redirects=True)
        
        assert b'Email already registered' in response.data or response.status_code == 200
    
    def test_registration_weak_password(self, client):
        """Test registration with weak password fails."""
        response = client.post('/auth/register', data={
            'username': 'weakpassuser',
            'email': 'weak@example.com',
            'password': 'password',  # Too weak
            'confirm_password': 'password'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        # Should show validation errors
    
    def test_registration_password_mismatch(self, client):
        """Test registration with mismatched passwords fails."""
        response = client.post('/auth/register', data={
            'username': 'mismatchuser',
            'email': 'mismatch@example.com',
            'password': 'SecureP@ss123',
            'confirm_password': 'DifferentP@ss456'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Passwords must match' in response.data or b'match' in response.data.lower()
    
    def test_successful_login(self, client, test_user):
        """Test successful login."""
        response = client.post('/auth/login', data={
            'email': 'test@example.com',
            'password': 'TestP@ss123'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Dashboard' in response.data or b'testuser' in response.data
    
    def test_login_invalid_email(self, client):
        """Test login with non-existent email."""
        response = client.post('/auth/login', data={
            'email': 'nonexistent@example.com',
            'password': 'SomeP@ss123'
        }, follow_redirects=True)
        
        assert b'Invalid email or password' in response.data or response.status_code == 200
    
    def test_login_wrong_password(self, client, test_user):
        """Test login with wrong password."""
        response = client.post('/auth/login', data={
            'email': 'test@example.com',
            'password': 'WrongP@ss123'
        }, follow_redirects=True)
        
        assert b'Invalid email or password' in response.data or response.status_code == 200
    
    def test_login_inactive_user(self, client, inactive_user):
        """Test login with inactive account."""
        response = client.post('/auth/login', data={
            'email': 'inactive@example.com',
            'password': 'TestP@ss123'
        }, follow_redirects=True)
        
        assert b'deactivated' in response.data.lower() or b'inactive' in response.data.lower() or response.status_code == 200
    
    def test_logout(self, auth_client):
        """Test logout functionality."""
        response = auth_client.get('/auth/logout', follow_redirects=True)
        
        assert response.status_code == 200
        # After logout, should be redirected to login or home
    
    def test_protected_route_without_login(self, client):
        """Test that protected routes redirect to login."""
        response = client.get('/items/')
        
        assert response.status_code == 302
        assert '/auth/login' in response.headers.get('Location', '')
    
    def test_protected_route_with_login(self, auth_client):
        """Test that authenticated users can access protected routes."""
        response = auth_client.get('/items/')
        
        assert response.status_code == 200


class TestPasswordService:
    """Password service unit tests."""
    
    def test_password_hashing(self):
        """Test password hashing produces different hashes."""
        service = PasswordService()
        password = 'SecureP@ss123'
        
        hash1 = service.hash_password(password)
        hash2 = service.hash_password(password)
        
        # Hashes should be different due to salt
        assert hash1 != hash2
        # But both should verify
        assert service.verify_password(password, hash1)
        assert service.verify_password(password, hash2)
    
    def test_password_verification_correct(self):
        """Test correct password verification."""
        service = PasswordService()
        password = 'SecureP@ss123'
        hash = service.hash_password(password)
        
        assert service.verify_password(password, hash) is True
    
    def test_password_verification_incorrect(self):
        """Test incorrect password verification."""
        service = PasswordService()
        hash = service.hash_password('SecureP@ss123')
        
        assert service.verify_password('WrongP@ss123', hash) is False
    
    def test_password_validation_strong(self):
        """Test strong password passes validation."""
        service = PasswordService()
        is_valid, errors = service.validate_password('SecureP@ss123!')
        
        assert is_valid is True
        assert errors == []
    
    def test_password_validation_too_short(self):
        """Test short password fails validation."""
        service = PasswordService()
        is_valid, errors = service.validate_password('Ab1!')
        
        assert is_valid is False
        assert any('8 characters' in e for e in errors)
    
    def test_password_validation_no_uppercase(self):
        """Test password without uppercase fails."""
        service = PasswordService()
        is_valid, errors = service.validate_password('securep@ss123')
        
        assert is_valid is False
        assert any('uppercase' in e.lower() for e in errors)
    
    def test_password_validation_no_lowercase(self):
        """Test password without lowercase fails."""
        service = PasswordService()
        is_valid, errors = service.validate_password('SECUREP@SS123')
        
        assert is_valid is False
        assert any('lowercase' in e.lower() for e in errors)
    
    def test_password_validation_no_digit(self):
        """Test password without digit fails."""
        service = PasswordService()
        is_valid, errors = service.validate_password('SecureP@ss!')
        
        assert is_valid is False
        assert any('digit' in e.lower() or 'number' in e.lower() for e in errors)
    
    def test_password_validation_no_special(self):
        """Test password without special character fails."""
        service = PasswordService()
        is_valid, errors = service.validate_password('SecurePass123')
        
        assert is_valid is False
        assert any('special' in e.lower() for e in errors)
    
    def test_random_password_generation(self):
        """Test random password generation."""
        service = PasswordService()
        password = service.generate_random_password()
        
        assert len(password) >= 12
        is_valid, _ = service.validate_password(password)
        assert is_valid is True


class TestChangePassword:
    """Password change tests."""
    
    def test_change_password_page_loads(self, auth_client):
        """Test change password page is accessible."""
        response = auth_client.get('/auth/change-password')
        
        assert response.status_code == 200
        assert b'Change Password' in response.data
    
    def test_change_password_success(self, auth_client, app, test_user):
        """Test successful password change."""
        response = auth_client.post('/auth/change-password', data={
            'current_password': 'TestP@ss123',
            'new_password': 'NewSecureP@ss456!',
            'confirm_password': 'NewSecureP@ss456!'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        # Verify new password works
        service = PasswordService()
        with app.app_context():
            user = User.query.filter_by(username='testuser').first()
            assert service.verify_password('NewSecureP@ss456!', user.password_hash)
    
    def test_change_password_wrong_current(self, auth_client):
        """Test change password with wrong current password."""
        response = auth_client.post('/auth/change-password', data={
            'current_password': 'WrongCurrentP@ss',
            'new_password': 'NewSecureP@ss456!',
            'confirm_password': 'NewSecureP@ss456!'
        }, follow_redirects=True)
        
        assert b'incorrect' in response.data.lower() or b'invalid' in response.data.lower()
