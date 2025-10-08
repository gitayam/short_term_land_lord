"""
Guest blueprint for guest invitation and registration functionality
"""

from flask import Blueprint

bp = Blueprint('guest', __name__, url_prefix='/guest')

from app.guest import routes