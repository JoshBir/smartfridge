"""
Password security service for SmartFridge application.

Provides secure password hashing using bcrypt and password validation.
"""

import re
from typing import Tuple, List

import bcrypt
from flask import current_app


class PasswordService:
    """
    Service class for password hashing and validation.
    
    Uses bcrypt with configurable work factor for secure password storage.
    """
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a password using bcrypt.
        
        Args:
            password: Plain text password.
        
        Returns:
            Bcrypt hash string.
        """
        work_factor = current_app.config.get('BCRYPT_WORK_FACTOR', 12)
        salt = bcrypt.gensalt(rounds=work_factor)
        password_hash = bcrypt.hashpw(password.encode('utf-8'), salt)
        return password_hash.decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """
        Verify a password against a bcrypt hash.
        
        Args:
            password: Plain text password to verify.
            password_hash: Stored bcrypt hash.
        
        Returns:
            True if password matches, False otherwise.
        """
        try:
            return bcrypt.checkpw(
                password.encode('utf-8'),
                password_hash.encode('utf-8')
            )
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def validate_password(password: str) -> Tuple[bool, List[str]]:
        """
        Validate password against security policy.
        
        Checks:
        - Minimum length (default: 8)
        - Uppercase letter requirement
        - Lowercase letter requirement
        - Digit requirement
        - Special character requirement
        
        Args:
            password: Password to validate.
        
        Returns:
            Tuple of (is_valid, list_of_errors).
        """
        errors: List[str] = []
        
        min_length = current_app.config.get('PASSWORD_MIN_LENGTH', 8)
        require_uppercase = current_app.config.get('PASSWORD_REQUIRE_UPPERCASE', True)
        require_lowercase = current_app.config.get('PASSWORD_REQUIRE_LOWERCASE', True)
        require_digit = current_app.config.get('PASSWORD_REQUIRE_DIGIT', True)
        require_special = current_app.config.get('PASSWORD_REQUIRE_SPECIAL', True)
        
        if len(password) < min_length:
            errors.append(f'Password must be at least {min_length} characters long.')
        
        if require_uppercase and not re.search(r'[A-Z]', password):
            errors.append('Password must contain at least one uppercase letter.')
        
        if require_lowercase and not re.search(r'[a-z]', password):
            errors.append('Password must contain at least one lowercase letter.')
        
        if require_digit and not re.search(r'\d', password):
            errors.append('Password must contain at least one digit.')
        
        if require_special and not re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\;\'`~]', password):
            errors.append('Password must contain at least one special character.')
        
        return (len(errors) == 0, errors)
    
    @staticmethod
    def generate_random_password(length: int = 16) -> str:
        """
        Generate a secure random password.
        
        Args:
            length: Password length (default: 16).
        
        Returns:
            Random password meeting all requirements.
        """
        import secrets
        import string
        
        # Ensure minimum requirements
        chars = [
            secrets.choice(string.ascii_uppercase),
            secrets.choice(string.ascii_lowercase),
            secrets.choice(string.digits),
            secrets.choice('!@#$%^&*()_+-=[]{}|;:,.<>?'),
        ]
        
        # Fill remaining length with random characters
        all_chars = string.ascii_letters + string.digits + '!@#$%^&*()_+-=[]{}|;:,.<>?'
        chars.extend(secrets.choice(all_chars) for _ in range(length - len(chars)))
        
        # Shuffle to avoid predictable positions
        secrets.SystemRandom().shuffle(chars)
        
        return ''.join(chars)
