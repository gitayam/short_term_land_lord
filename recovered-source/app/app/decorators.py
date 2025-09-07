from functools import wraps
from flask import current_app, request, flash, redirect, url_for
from app.models import AdminAction, db
from datetime import datetime
from flask_login import current_user

def log_admin_action(action_type):
    """
    Decorator to log administrative actions in the database.
    
    Args:
        action_type (str): The type of action being performed (e.g., 'delete', 'suspend', 'reset_password')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get the current user (admin) and target user from the function arguments
            admin = kwargs.get('current_user')
            target_user_id = kwargs.get('user_id')
            
            # Call the original function
            result = f(*args, **kwargs)
            
            # Log the action if we have both admin and target user
            if admin and target_user_id:
                try:
                    action = AdminAction(
                        admin_id=admin.id,
                        target_user_id=target_user_id,
                        action_type=action_type,
                        action_details=f"{action_type.capitalize()} action performed by {admin.email}",
                        ip_address=request.remote_addr,
                        created_at=datetime.utcnow()
                    )
                    db.session.add(action)
                    db.session.commit()
                except Exception as e:
                    current_app.logger.error(f"Failed to log admin action: {str(e)}")
                    db.session.rollback()
            
            return result
        return decorated_function
    return decorator

def property_owner_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_property_owner:
            flash('You must be a property owner to access this page.', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

def admin_or_owner_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not (current_user.is_admin or current_user.is_property_owner):
            flash('You must be an admin or property owner to access this page.', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function 