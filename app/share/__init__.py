from flask import Blueprint

bp = Blueprint('share', __name__, url_prefix='/share')

from app.share import routes