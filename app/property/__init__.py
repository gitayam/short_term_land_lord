from flask import Blueprint

bp = Blueprint('property', __name__)

from app.property import routes
