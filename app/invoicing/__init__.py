from flask import Blueprint

bp = Blueprint('invoicing', __name__)

from app.invoicing import routes
