"""
Authentication blueprint for SmartFridge application.

Handles user registration, login, logout, and password management.
"""

from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user

from app.extensions import db, limiter
from app.models.user import User
from app.forms.auth import (
    LoginForm,
    RegistrationForm,
    ChangePasswordForm,
)


auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration page."""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = RegistrationForm()
    
    if form.validate_on_submit():
        user = User.create(
            username=form.username.data,
            email=form.email.data,
            password=form.password.data
        )
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html', form=form)


@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute", methods=['POST'])
def login():
    """User login page."""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        user = User.get_by_username(form.username.data)
        
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password.', 'danger')
            return render_template('auth/login.html', form=form)
        
        if not user.is_active:
            flash('Your account has been deactivated. Please contact support.', 'warning')
            return render_template('auth/login.html', form=form)
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        login_user(user, remember=form.remember_me.data)
        
        # Handle next URL for protected pages
        next_page = request.args.get('next')
        if next_page and next_page.startswith('/'):
            return redirect(next_page)
        
        flash(f'Welcome back, {user.username}!', 'success')
        return redirect(url_for('main.dashboard'))
    
    return render_template('auth/login.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    """Log out the current user."""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))


@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Change password page."""
    form = ChangePasswordForm()
    
    if form.validate_on_submit():
        if not current_user.check_password(form.current_password.data):
            flash('Current password is incorrect.', 'danger')
            return render_template('auth/change_password.html', form=form)
        
        current_user.set_password(form.new_password.data)
        db.session.commit()
        
        flash('Your password has been updated.', 'success')
        return redirect(url_for('main.dashboard'))
    
    return render_template('auth/change_password.html', form=form)


@auth_bp.route('/profile')
@login_required
def profile():
    """User profile page."""
    return render_template('auth/profile.html')
