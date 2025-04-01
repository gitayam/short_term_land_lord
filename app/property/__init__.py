from flask import Blueprint

bp = Blueprint('property', __name__)

from app.property import routes
from app.property import guest_reviews

# Register guest review routes
guest_reviews.register_guest_review_routes(bp)