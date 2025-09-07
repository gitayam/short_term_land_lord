from flask import Blueprint

bp = Blueprint('messages', __name__)

from app.messages import routes 