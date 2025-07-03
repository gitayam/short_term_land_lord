from functools import wraps
from flask import flash, redirect, url_for, request
from flask_login import current_user, login_required
from app.models import UserRoles, TaskAssignment, CleaningSession, ServiceType
from app.models_modules.invoicing import Invoice

def property_owner_required(f):
    """Decorator for routes that require property owner access."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if not current_user.is_property_owner:
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
        if not (current_user.is_property_owner or current_user.is_property_manager or current_user.has_admin_role):
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
    """Decorator to ensure only users who can manage or view invoices can access a route"""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        # Allow property owner, manager, or admin
        if current_user.is_property_owner or current_user.is_property_manager or current_user.has_admin_role:
            return f(*args, **kwargs)
        # Allow maintenance staff or cleaner if they have worked on any invoice's property
        invoice_id = kwargs.get('id') or kwargs.get('invoice_id')
        if invoice_id:
            invoice = Invoice.query.get(invoice_id)
            if not invoice:
                flash('Invoice not found.', 'danger')
                return redirect(url_for('main.index'))
            # Check if user has a task assignment or cleaning session for this property
            has_task = TaskAssignment.query.filter_by(user_id=current_user.id).join('task').filter_by(property_id=invoice.property_id).first()
            has_cleaning = False
            if hasattr(current_user, 'is_cleaner') and current_user.is_cleaner:
                has_cleaning = CleaningSession.query.filter_by(cleaner_id=current_user.id, property_id=invoice.property_id).first() is not None
            if has_task or has_cleaning:
                return f(*args, **kwargs)
        flash('Access denied. You do not have permission to view this invoice.', 'danger')
        return redirect(url_for('main.index'))
    return decorated_function

def workforce_management_required(f):
    """Decorator for routes that require workforce management access."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if not (current_user.is_property_owner or current_user.is_property_manager or current_user.is_admin):
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
        if not (current_user.is_property_owner or current_user.is_property_manager or current_user.is_admin):
            flash('You do not have access to inventory management.', 'danger')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated_function