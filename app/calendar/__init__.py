from flask import Blueprint

bp = Blueprint('calendar', __name__, url_prefix='/calendar')

from app.calendar import routes 