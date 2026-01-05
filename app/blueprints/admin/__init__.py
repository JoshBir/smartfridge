"""
Admin blueprint for SmartFridge application.

Handles user management and system administration.
"""

from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user

from app.extensions import db
from app.models.user import User, UserRole
from app.forms.admin import (
    UserEditForm,
    AdminResetPasswordForm,
    CreateUserForm,
    UserSearchForm,
)
from app.services.security.password import PasswordService


admin_bp = Blueprint('admin', __name__)


def admin_required(f):
    """Decorator to require admin role."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


@admin_bp.route('/')
@login_required
@admin_required
def index():
    """Admin dashboard."""
    from app.models.item import Item
    from app.models.recipe import Recipe
    from app.models.site import Site
    
    # Get statistics
    stats = {
        'total_users': User.query.count(),
        'active_users': User.query.filter_by(is_active=True, is_approved=True).count(),
        'admin_users': User.query.filter_by(role=UserRole.ADMIN.value).count(),
        'pending_users': User.query.filter_by(is_approved=False).count(),
        'total_items': Item.query.count(),
        'total_recipes': Recipe.query.count(),
        'total_sites': Site.query.count(),
        'expired_items': Item.query.filter(Item.expiry_date < db.func.current_date()).count(),
        'ai_recipes': Recipe.query.filter_by(is_ai_generated=True).count(),
    }
    
    # Recent users
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    
    # Pending approval users
    pending_approval = User.get_pending_users()[:5]  # Show first 5
    
    return render_template(
        'admin/index.html',
        stats=stats,
        recent_users=recent_users,
        pending_approval=pending_approval,
    )


@admin_bp.route('/users')
@login_required
@admin_required
def users():
    """List all users."""
    form = UserSearchForm(request.args, meta={'csrf': False})
    
    query = User.query
    
    if form.search.data:
        search_term = f'%{form.search.data}%'
        query = query.filter(
            (User.username.ilike(search_term)) |
            (User.email.ilike(search_term))
        )
    
    if form.role.data:
        query = query.filter_by(role=form.role.data)
    
    if form.status.data:
        if form.status.data == 'active':
            query = query.filter_by(is_active=True)
        elif form.status.data == 'inactive':
            query = query.filter_by(is_active=False)
    
    users = query.order_by(User.created_at.desc()).all()
    
    return render_template('admin/users.html', users=users, form=form)


@admin_bp.route('/users/new', methods=['GET', 'POST'])
@login_required
@admin_required
def create_user():
    """Create a new user."""
    form = CreateUserForm()
    
    if form.validate_on_submit():
        user = User.create(
            username=form.username.data,
            email=form.email.data,
            password=form.password.data,
            role=form.role.data,
            is_approved=True  # Admin-created users are auto-approved
        )
        
        flash(f'User "{user.username}" has been created.', 'success')
        return redirect(url_for('admin.users'))
    
    return render_template('admin/user_form.html', form=form, title='Create User')


@admin_bp.route('/users/<int:id>')
@login_required
@admin_required
def view_user(id):
    """View user details."""
    user = User.query.get_or_404(id)
    return render_template('admin/user_view.html', user=user)


@admin_bp.route('/users/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(id):
    """Edit user details."""
    user = User.query.get_or_404(id)
    
    form = UserEditForm(user_id=user.id, obj=user)
    
    if form.validate_on_submit():
        # Prevent removing the last admin
        if (user.is_admin and 
            form.role.data != UserRole.ADMIN.value and
            User.query.filter_by(role=UserRole.ADMIN.value).count() == 1):
            flash('Cannot remove the last administrator.', 'danger')
            return render_template('admin/user_form.html', form=form, user=user, title='Edit User')
        
        user.username = form.username.data
        user.email = form.email.data.lower()
        user.role = form.role.data
        user.is_active = form.is_active.data
        
        db.session.commit()
        
        flash(f'User "{user.username}" has been updated.', 'success')
        return redirect(url_for('admin.users'))
    
    return render_template('admin/user_form.html', form=form, user=user, title='Edit User')


@admin_bp.route('/users/<int:id>/reset-password', methods=['GET', 'POST'])
@login_required
@admin_required
def reset_password(id):
    """Reset a user's password."""
    user = User.query.get_or_404(id)
    
    form = AdminResetPasswordForm()
    
    if form.validate_on_submit():
        user.set_password(form.new_password.data)
        db.session.commit()
        
        flash(f'Password for "{user.username}" has been reset.', 'success')
        return redirect(url_for('admin.view_user', id=user.id))
    
    return render_template('admin/reset_password.html', form=form, user=user)


@admin_bp.route('/users/<int:id>/deactivate', methods=['POST'])
@login_required
@admin_required
def deactivate_user(id):
    """Deactivate a user account."""
    user = User.query.get_or_404(id)
    
    # Prevent self-deactivation
    if user.id == current_user.id:
        flash('You cannot deactivate your own account.', 'danger')
        return redirect(url_for('admin.users'))
    
    # Prevent deactivating the last admin
    if (user.is_admin and
        User.query.filter_by(role=UserRole.ADMIN.value, is_active=True).count() == 1):
        flash('Cannot deactivate the last active administrator.', 'danger')
        return redirect(url_for('admin.users'))
    
    user.deactivate()
    
    flash(f'User "{user.username}" has been deactivated.', 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/users/<int:id>/activate', methods=['POST'])
@login_required
@admin_required
def activate_user(id):
    """Activate a user account."""
    user = User.query.get_or_404(id)
    
    user.activate()
    
    flash(f'User "{user.username}" has been activated.', 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/users/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(id):
    """Delete a user account."""
    user = User.query.get_or_404(id)
    
    # Prevent self-deletion
    if user.id == current_user.id:
        flash('You cannot delete your own account.', 'danger')
        return redirect(url_for('admin.users'))
    
    # Prevent deleting the last admin
    if (user.is_admin and
        User.query.filter_by(role=UserRole.ADMIN.value).count() == 1):
        flash('Cannot delete the last administrator.', 'danger')
        return redirect(url_for('admin.users'))
    
    username = user.username
    db.session.delete(user)
    db.session.commit()
    
    flash(f'User "{username}" has been deleted.', 'success')
    return redirect(url_for('admin.users'))


# ============================================================================
# User Approval Management
# ============================================================================

@admin_bp.route('/users/pending')
@login_required
@admin_required
def pending_users():
    """List all users pending approval."""
    users = User.get_pending_users()
    return render_template('admin/pending_users.html', users=users)


@admin_bp.route('/users/<int:id>/approve', methods=['POST'])
@login_required
@admin_required
def approve_user(id):
    """Approve a user registration."""
    user = User.query.get_or_404(id)
    
    if user.is_approved:
        flash(f'User "{user.username}" is already approved.', 'info')
        return redirect(url_for('admin.pending_users'))
    
    user.approve()
    
    flash(f'User "{user.username}" has been approved and can now log in.', 'success')
    return redirect(url_for('admin.pending_users'))


@admin_bp.route('/users/<int:id>/reject', methods=['POST'])
@login_required
@admin_required
def reject_user(id):
    """Reject a user registration (deletes the account)."""
    user = User.query.get_or_404(id)
    
    if user.is_approved:
        flash(f'User "{user.username}" is already approved. Use delete instead.', 'warning')
        return redirect(url_for('admin.users'))
    
    username = user.username
    user.reject()
    
    flash(f'User "{username}" registration has been rejected and removed.', 'success')
    return redirect(url_for('admin.pending_users'))


@admin_bp.route('/users/approve-all', methods=['POST'])
@login_required
@admin_required
def approve_all_users():
    """Approve all pending user registrations."""
    pending = User.get_pending_users()
    
    if not pending:
        flash('No pending users to approve.', 'info')
        return redirect(url_for('admin.pending_users'))
    
    count = 0
    for user in pending:
        user.is_approved = True
        count += 1
    
    db.session.commit()
    
    flash(f'{count} user(s) have been approved.', 'success')
    return redirect(url_for('admin.pending_users'))
