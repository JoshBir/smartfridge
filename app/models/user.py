"""
User model for SmartFridge application.

Handles user authentication, roles, and profile data.
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from flask_login import UserMixin
from sqlalchemy import Index

from app.extensions import db
from app.services.security.password import PasswordService


class UserRole(str, Enum):
    """User role enumeration."""
    ADMIN = 'admin'
    USER = 'user'


class User(UserMixin, db.Model):
    """
    User model for authentication and authorisation.
    
    Attributes:
        id: Primary key.
        username: Unique username for login.
        email: Unique email address.
        password_hash: Bcrypt-hashed password.
        role: User role (admin or user).
        is_active: Whether the account is active.
        created_at: Account creation timestamp.
        last_login: Last successful login timestamp.
    """
    
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), default=UserRole.USER.value, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_approved = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_login = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    items = db.relationship('Item', backref='owner', lazy='dynamic',
                           cascade='all, delete-orphan')
    recipes = db.relationship('Recipe', backref='owner', lazy='dynamic',
                             cascade='all, delete-orphan')
    sites = db.relationship('Site', backref='owner', lazy='dynamic',
                           cascade='all, delete-orphan')
    
    def __repr__(self) -> str:
        return f'<User {self.username}>'
    
    def set_password(self, password: str) -> None:
        """
        Hash and set the user's password.
        
        Args:
            password: Plain text password to hash.
        """
        self.password_hash = PasswordService.hash_password(password)
    
    def check_password(self, password: str) -> bool:
        """
        Verify a password against the stored hash.
        
        Args:
            password: Plain text password to verify.
        
        Returns:
            True if password matches, False otherwise.
        """
        return PasswordService.verify_password(password, self.password_hash)
    
    @property
    def is_admin(self) -> bool:
        """Check if user has admin role."""
        return self.role == UserRole.ADMIN.value
    
    def update_last_login(self) -> None:
        """Update the last login timestamp."""
        self.last_login = datetime.utcnow()
        db.session.commit()
    
    def deactivate(self) -> None:
        """Deactivate the user account."""
        self.is_active = False
        db.session.commit()
    
    def activate(self) -> None:
        """Activate the user account."""
        self.is_active = True
        db.session.commit()
    
    def approve(self) -> None:
        """Approve the user account (admin approval for registration)."""
        self.is_approved = True
        db.session.commit()
    
    def reject(self) -> None:
        """Reject the user account (admin rejection for registration)."""
        db.session.delete(self)
        db.session.commit()
    
    @property
    def is_pending_approval(self) -> bool:
        """Check if user is pending admin approval."""
        return not self.is_approved
    
    @classmethod
    def get_pending_users(cls) -> list:
        """Get all users pending approval."""
        return cls.query.filter_by(is_approved=False).order_by(cls.created_at.asc()).all()
    
    @classmethod
    def get_by_username(cls, username: str) -> Optional['User']:
        """
        Find a user by username.
        
        Args:
            username: Username to search for.
        
        Returns:
            User instance or None.
        """
        return cls.query.filter_by(username=username).first()
    
    @classmethod
    def get_by_email(cls, email: str) -> Optional['User']:
        """
        Find a user by email.
        
        Args:
            email: Email to search for.
        
        Returns:
            User instance or None.
        """
        return cls.query.filter_by(email=email.lower()).first()
    
    @classmethod
    def create(cls, username: str, email: str, password: str,
               role: UserRole = UserRole.USER, is_approved: bool = False) -> 'User':
        """
        Create a new user.
        
        Args:
            username: Unique username.
            email: Unique email address.
            password: Plain text password.
            role: User role (defaults to USER).
            is_approved: Whether the user is pre-approved (defaults to False).
        
        Returns:
            Created User instance.
        """
        user = cls(
            username=username,
            email=email.lower(),
            role=role.value if isinstance(role, UserRole) else role,
            is_approved=is_approved,
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return user


# Indexes for common queries
Index('idx_users_username_active', User.username, User.is_active)
Index('idx_users_email_active', User.email, User.is_active)
