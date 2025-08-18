from flask import Blueprint

bp = Blueprint('admin', __name__)

from app.admin import routes

# Register configuration management blueprint
from app.admin.config_routes import bp as config_bp 