"""
Admin forms for SmartFridge application.
"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, Optional, Email, EqualTo, ValidationError

from app.models.user import User, UserRole


class UserEditForm(FlaskForm):
    """Form for admin to edit user details."""
    
    username = StringField(
        'Username',
        validators=[
            DataRequired(message='Username is required.'),
            Length(min=3, max=64, message='Username must be between 3 and 64 characters.')
        ]
    )
    
    email = StringField(
        'Email',
        validators=[
            DataRequired(message='Email is required.'),
            Email(message='Please enter a valid email address.')
        ]
    )
    
    role = SelectField(
        'Role',
        choices=[
            (UserRole.USER.value, 'User'),
            (UserRole.ADMIN.value, 'Admin'),
        ]
    )
    
    is_active = BooleanField('Active')
    
    submit = SubmitField('Save Changes')
    
    def __init__(self, user_id=None, *args, **kwargs):
        """
        Initialise form with user context.
        
        Args:
            user_id: User ID being edited (for validation).
        """
        super().__init__(*args, **kwargs)
        self.user_id = user_id
    
    def validate_username(self, field):
        """Check username is unique."""
        user = User.get_by_username(field.data)
        if user and user.id != self.user_id:
            raise ValidationError('This username is already taken.')
    
    def validate_email(self, field):
        """Check email is unique."""
        user = User.get_by_email(field.data)
        if user and user.id != self.user_id:
            raise ValidationError('This email is already registered.')


class AdminResetPasswordForm(FlaskForm):
    """Form for admin to reset user password."""
    
    new_password = PasswordField(
        'New Password',
        validators=[
            DataRequired(message='Please enter a new password.'),
            Length(min=8, message='Password must be at least 8 characters.')
        ],
        render_kw={'placeholder': 'Enter new password'}
    )
    
    confirm_password = PasswordField(
        'Confirm Password',
        validators=[
            DataRequired(message='Please confirm the password.'),
            EqualTo('new_password', message='Passwords must match.')
        ],
        render_kw={'placeholder': 'Confirm new password'}
    )
    
    submit = SubmitField('Reset Password')


class CreateUserForm(FlaskForm):
    """Form for admin to create a new user."""
    
    username = StringField(
        'Username',
        validators=[
            DataRequired(message='Username is required.'),
            Length(min=3, max=64, message='Username must be between 3 and 64 characters.')
        ],
        render_kw={'placeholder': 'Enter username', 'autofocus': True}
    )
    
    email = StringField(
        'Email',
        validators=[
            DataRequired(message='Email is required.'),
            Email(message='Please enter a valid email address.')
        ],
        render_kw={'placeholder': 'Enter email address'}
    )
    
    password = PasswordField(
        'Password',
        validators=[
            DataRequired(message='Password is required.'),
            Length(min=8, message='Password must be at least 8 characters.')
        ],
        render_kw={'placeholder': 'Enter password'}
    )
    
    role = SelectField(
        'Role',
        choices=[
            (UserRole.USER.value, 'User'),
            (UserRole.ADMIN.value, 'Admin'),
        ],
        default=UserRole.USER.value
    )
    
    submit = SubmitField('Create User')
    
    def validate_username(self, field):
        """Check username is unique."""
        if User.get_by_username(field.data):
            raise ValidationError('This username is already taken.')
    
    def validate_email(self, field):
        """Check email is unique."""
        if User.get_by_email(field.data):
            raise ValidationError('This email is already registered.')


class UserSearchForm(FlaskForm):
    """Form for searching users."""
    
    search = StringField(
        'Search',
        validators=[Optional()],
        render_kw={'placeholder': 'Search users...'}
    )
    
    role = SelectField(
        'Role',
        choices=[
            ('', 'All Roles'),
            (UserRole.USER.value, 'Users'),
            (UserRole.ADMIN.value, 'Admins'),
        ],
        default=''
    )
    
    status = SelectField(
        'Status',
        choices=[
            ('', 'All Statuses'),
            ('active', 'Active'),
            ('inactive', 'Inactive'),
        ],
        default=''
    )
    
    submit = SubmitField('Filter')
