from flask import Blueprint

bp = Blueprint('workforce', __name__)

from app.workforce import routes
