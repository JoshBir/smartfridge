"""
Authentication forms for SmartFridge application.
"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import (
    DataRequired, Email, EqualTo, Length, ValidationError, Regexp
)

from app.models.user import User


class LoginForm(FlaskForm):
    """User login form."""
    
    username = StringField(
        'Username',
        validators=[
            DataRequired(message='Please enter your username.'),
            Length(min=3, max=64, message='Username must be between 3 and 64 characters.')
        ],
        render_kw={'placeholder': 'Enter your username', 'autofocus': True}
    )
    
    password = PasswordField(
        'Password',
        validators=[
            DataRequired(message='Please enter your password.')
        ],
        render_kw={'placeholder': 'Enter your password'}
    )
    
    remember_me = BooleanField('Remember me')
    
    submit = SubmitField('Log In')


class RegistrationForm(FlaskForm):
    """User registration form."""
    
    username = StringField(
        'Username',
        validators=[
            DataRequired(message='Please choose a username.'),
            Length(min=3, max=64, message='Username must be between 3 and 64 characters.'),
            Regexp(
                r'^[A-Za-z][A-Za-z0-9_.]*$',
                message='Username must start with a letter and contain only letters, numbers, dots, or underscores.'
            )
        ],
        render_kw={'placeholder': 'Choose a username', 'autofocus': True}
    )
    
    email = StringField(
        'Email',
        validators=[
            DataRequired(message='Please enter your email address.'),
            Email(message='Please enter a valid email address.'),
            Length(max=120, message='Email must be less than 120 characters.')
        ],
        render_kw={'placeholder': 'Enter your email address'}
    )
    
    password = PasswordField(
        'Password',
        validators=[
            DataRequired(message='Please choose a password.'),
            Length(min=8, message='Password must be at least 8 characters long.')
        ],
        render_kw={'placeholder': 'Choose a strong password'}
    )
    
    password2 = PasswordField(
        'Confirm Password',
        validators=[
            DataRequired(message='Please confirm your password.'),
            EqualTo('password', message='Passwords must match.')
        ],
        render_kw={'placeholder': 'Confirm your password'}
    )
    
    submit = SubmitField('Register')
    
    def validate_username(self, field):
        """Check username is unique."""
        if User.get_by_username(field.data):
            raise ValidationError('This username is already taken.')
    
    def validate_email(self, field):
        """Check email is unique."""
        if User.get_by_email(field.data):
            raise ValidationError('This email address is already registered.')
    
    def validate_password(self, field):
        """Validate password strength."""
        password = field.data
        errors = []
        
        if not any(c.isupper() for c in password):
            errors.append('at least one uppercase letter')
        if not any(c.islower() for c in password):
            errors.append('at least one lowercase letter')
        if not any(c.isdigit() for c in password):
            errors.append('at least one digit')
        if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password):
            errors.append('at least one special character')
        
        if errors:
            raise ValidationError(f'Password must contain {", ".join(errors)}.')


class ChangePasswordForm(FlaskForm):
    """Change password form."""
    
    current_password = PasswordField(
        'Current Password',
        validators=[
            DataRequired(message='Please enter your current password.')
        ],
        render_kw={'placeholder': 'Enter your current password', 'autofocus': True}
    )
    
    new_password = PasswordField(
        'New Password',
        validators=[
            DataRequired(message='Please enter a new password.'),
            Length(min=8, message='Password must be at least 8 characters long.')
        ],
        render_kw={'placeholder': 'Enter a new password'}
    )
    
    new_password2 = PasswordField(
        'Confirm New Password',
        validators=[
            DataRequired(message='Please confirm your new password.'),
            EqualTo('new_password', message='Passwords must match.')
        ],
        render_kw={'placeholder': 'Confirm your new password'}
    )
    
    submit = SubmitField('Change Password')
    
    def validate_new_password(self, field):
        """Validate password strength."""
        password = field.data
        errors = []
        
        if not any(c.isupper() for c in password):
            errors.append('at least one uppercase letter')
        if not any(c.islower() for c in password):
            errors.append('at least one lowercase letter')
        if not any(c.isdigit() for c in password):
            errors.append('at least one digit')
        if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password):
            errors.append('at least one special character')
        
        if errors:
            raise ValidationError(f'Password must contain {", ".join(errors)}.')


class RequestPasswordResetForm(FlaskForm):
    """Request password reset form."""
    
    email = StringField(
        'Email',
        validators=[
            DataRequired(message='Please enter your email address.'),
            Email(message='Please enter a valid email address.')
        ],
        render_kw={'placeholder': 'Enter your registered email', 'autofocus': True}
    )
    
    submit = SubmitField('Request Password Reset')


class ResetPasswordForm(FlaskForm):
    """Reset password form."""
    
    password = PasswordField(
        'New Password',
        validators=[
            DataRequired(message='Please enter a new password.'),
            Length(min=8, message='Password must be at least 8 characters long.')
        ],
        render_kw={'placeholder': 'Enter a new password', 'autofocus': True}
    )
    
    password2 = PasswordField(
        'Confirm Password',
        validators=[
            DataRequired(message='Please confirm your new password.'),
            EqualTo('password', message='Passwords must match.')
        ],
        render_kw={'placeholder': 'Confirm your new password'}
    )
    
    submit = SubmitField('Reset Password')
