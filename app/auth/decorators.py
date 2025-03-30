from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user, login_required
from app.models import UserRoles

def property_owner_required(f):
    """Decorator to ensure only property owners can access a route"""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_property_owner():
            flash('Access denied. You must be a property owner to view this page.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

def property_manager_required(f):
    """Decorator to ensure only property managers, owners, or admins can access a route"""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not (current_user.is_property_manager() or current_user.is_property_owner() or current_user.is_admin()):
            flash('Access denied. You must be a property manager, property owner, or admin to view this page.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to ensure only admins can access a route"""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.role == UserRoles.ADMIN:
            flash('Access denied. You must be an admin to view this page.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function 

def invoice_access_required(f):
    """Decorator to ensure only users who can manage invoices can access a route"""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not (current_user.is_property_owner() or current_user.is_property_manager() or current_user.is_admin()):
            flash('Access denied. You must be a property owner, property manager, or admin to view this page.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function