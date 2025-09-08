import secrets
from flask import Blueprint, jsonify, request, make_response, render_template, current_app, flash, redirect, url_for
from flask_login import current_user, login_required
from app import db
from app.models import Property, RecommendationBlock
from app.utils.zillow_scraper import fetch_zillow_details
import logging
import flask

# Set log level to DEBUG for troubleshooting
flask.current_app = None  # Avoids issues if not in app context
logging.basicConfig(level=logging.DEBUG)

bp = Blueprint('property_routes', __name__)

@bp.route('/property/<int:property_id>/view', methods=['GET'])
@login_required
def view_property(property_id):
    """View property details."""
    property = Property.query.get_or_404(property_id)
    
    # Check if user has permission to view this property
    if not current_user.is_admin and property.owner_id != current_user.id:
        flash('You do not have permission to view this property.', 'danger')
        return redirect(url_for('main.index'))
    
    return render_template('property/view.html', property=property)

@bp.route('/property/<token>/guide', methods=['GET'])
def public_guide_book(token):
    """Public access to a property's guide book via token."""
    property = Property.query.filter_by(guide_book_token=token).first_or_404()
    
    # Get or create guest token from cookie
    guest_token = request.cookies.get('guest_token')
    if not guest_token:
        guest_token = secrets.token_urlsafe(32)
    
    # Get recommendations for this property
    recommendations = RecommendationBlock.query.filter_by(
        property_id=property.id
    ).order_by(RecommendationBlock.created_at.desc()).all()
    
    response = make_response(render_template(
        'property/public_guide.html',
        property=property,
        recommendations=recommendations,
        guest_token=guest_token
    ))
    
    # Set cookie if it doesn't exist
    if not request.cookies.get('guest_token'):
        response.set_cookie('guest_token', guest_token, max_age=30*24*60*60)  # 30 days
    
    return response

@bp.route('/api/recommendations/<int:recommendation_id>/vote', methods=['POST'])
def toggle_recommendation_vote(recommendation_id):
    """Toggle a vote for a recommendation."""
    guest_token = request.headers.get('X-Guest-Token')
    if not guest_token:
        return jsonify({'error': 'Guest token required'}), 400
    
    recommendation = RecommendationBlock.query.get_or_404(recommendation_id)
    voted = recommendation.toggle_vote(guest_token)
    
    return jsonify({
        'voted': voted,
        'vote_count': recommendation.vote_count
    })

@bp.route('/api/recommendations/<int:recommendation_id>/staff-pick', methods=['POST'])
def toggle_staff_pick(recommendation_id):
    """Toggle staff pick status for a recommendation."""
    if not current_user.is_authenticated or not (current_user.is_property_owner or current_user.has_admin_role):
        return jsonify({'error': 'Unauthorized'}), 403
    
    recommendation = RecommendationBlock.query.get_or_404(recommendation_id)
    
    # Verify the user owns this property or is an admin
    if not current_user.has_admin_role and recommendation.property.owner_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    recommendation.staff_pick = not recommendation.staff_pick
    db.session.commit()
    
    return jsonify({
        'staff_pick': recommendation.staff_pick
    })

@bp.route('/api/fetch_zillow', methods=['POST'])
def fetch_zillow():
    """
    Legacy endpoint - redirect to new enhanced Zillow API
    """
    return jsonify({
        'error': 'This endpoint is deprecated. Please use /api/zillow/property-data instead.',
        'message': 'The Zillow scraper has been enhanced. Update your client to use the new endpoint.'
    }), 410 