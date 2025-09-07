from flask import Blueprint

bp = Blueprint('property', __name__)

from . import routes, filters

# Register template filters
bp.add_app_template_filter(filters.format_next_collection, 'format_next_collection')

from app.property import guest_reviews

# Register guest review routes
guest_reviews.register_guest_review_routes(bp)

from . import routes  # This import must be at the bottom to avoid circular imports