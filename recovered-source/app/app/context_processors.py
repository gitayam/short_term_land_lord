from flask_login import current_user
from app.models import Property

def admin_properties():
    """Context processor to provide properties for admin users"""
    if current_user.is_authenticated and current_user.has_admin_role:
        return {'admin_properties': Property.query.all()}
    return {'admin_properties': []}

def user_theme():
    """Context processor to provide user's theme preference"""
    if current_user.is_authenticated:
        theme = current_user.theme_preference or 'light'
        return {'user_theme': theme}
    return {'user_theme': 'light'}  # Default theme for non-authenticated users 