from flask import Blueprint

bp = Blueprint('sms', __name__)

from app.sms import routes 