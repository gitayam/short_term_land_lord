from flask import Blueprint

bp = Blueprint('guidebook', __name__)

from app.guidebook import routes