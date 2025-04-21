"""Admin module for managing site settings and user administration."""
from flask import Blueprint

bp = Blueprint('admin', __name__)

from app.admin import routes
