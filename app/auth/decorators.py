from functools import wraps
from flask import flash, redirect, url_for, request
from flask_login import current_user, login_required
from app.models import UserRoles

def property_owner_required(f):
    """Decorator for routes that require property owner access."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if not current_user.is_property_owner():
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

def property_manager_required(f):
    """Decorator for routes that require property manager or above access."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login', next=request.url))
        if not (current_user.is_property_manager or current_user.is_property_owner or current_user.is_admin):
            flash('You do not have access to this page.', 'danger')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator for routes that require admin access."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if not current_user.is_admin:
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

def invoice_access_required(f):
    """Decorator to ensure only users who can manage invoices can access a route"""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not (current_user.is_property_owner() or current_user.is_property_manager() or current_user.is_admin):
            flash('Access denied. You must be a property owner, property manager, or admin to view this page.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

def workforce_management_required(f):
    """Decorator for routes that require workforce management access."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if not (current_user.is_property_owner() or current_user.is_property_manager or current_user.is_admin):
            flash('You do not have permission to access the workforce management section.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

def inventory_management_required(f):
    """Decorator for routes that require inventory management access."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login', next=request.url))
        if not (current_user.is_property_owner() or current_user.is_property_manager or current_user.is_admin):
            flash('You do not have access to inventory management.', 'danger')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated_function