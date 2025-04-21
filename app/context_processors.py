from flask_login import current_user
from app.models import Property

def admin_properties():
    """Context processor to provide properties for admin users"""
    if current_user.is_authenticated and current_user.has_admin_role:
        return {'admin_properties': Property.query.all()}
    return {'admin_properties': []} 