import secrets
from flask import Blueprint, jsonify, request, make_response, render_template, current_app, flash, redirect, url_for
from flask_login import current_user, login_required
from app import db
from app.models import Property, RecommendationBlock
from app.services.property_data_service import PropertyDataIntegrationService
from app.services.manual_entry_helper import ManualEntryHelper
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
    Legacy endpoint - now uses new property data integration service
    """
    return jsonify({
        'error': 'This endpoint is deprecated. Please use /api/property/suggestions instead.',
        'message': 'Property data collection has been enhanced with RentCast API and manual entry assistance.'
    }), 410

@bp.route('/api/property/suggestions', methods=['POST'])
@login_required
def get_property_suggestions():
    """
    Get property suggestions using RentCast API with scraper fallback.
    Replaces the old Zillow scraper with more reliable data sources.
    """
    try:
        data = request.get_json()
        address_or_url = data.get('address_or_url', '').strip()
        
        if not address_or_url:
            return jsonify({
                'success': False,
                'error': 'Address or URL is required'
            }), 400
        
        # Initialize property data service
        property_service = PropertyDataIntegrationService()
        
        # Get property suggestions
        result = property_service.get_property_suggestions(address_or_url)
        
        if result['success']:
            return jsonify({
                'success': True,
                'data': result['preview'],
                'source': result['source'],
                'suggestions': result['suggestions']
            })
        else:
            # If automated sources fail, provide manual entry assistance
            manual_data = ManualEntryHelper.parse_address(address_or_url)
            property_types = ManualEntryHelper.get_property_type_suggestions()
            help_text = ManualEntryHelper.get_form_help_text()
            
            return jsonify({
                'success': False,
                'error': result.get('error', 'Property data not found'),
                'manual_entry': {
                    'parsed_address': manual_data,
                    'property_types': property_types,
                    'help_text': help_text,
                    'suggestions': {
                        'max_guests_2br': ManualEntryHelper.estimate_max_guests(2),
                        'max_guests_3br': ManualEntryHelper.estimate_max_guests(3),
                        'cleaning_fee_2br2ba': ManualEntryHelper.suggest_cleaning_fee(2, 2),
                        'cleaning_fee_3br2ba': ManualEntryHelper.suggest_cleaning_fee(3, 2)
                    }
                }
            })
            
    except Exception as e:
        logging.error(f"Error in property suggestions endpoint: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to process request: {str(e)}'
        }), 500

@bp.route('/api/property/validate', methods=['POST'])
@login_required
def validate_property_data():
    """
    Validate property data before submission.
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        is_valid, missing_fields = ManualEntryHelper.validate_required_fields(data)
        
        response = {
            'valid': is_valid,
            'missing_fields': missing_fields
        }
        
        # Add suggestions if data is provided
        if data.get('bedrooms'):
            response['suggested_max_guests'] = ManualEntryHelper.estimate_max_guests(data['bedrooms'])
        
        if data.get('bedrooms') and data.get('bathrooms'):
            response['suggested_cleaning_fee'] = ManualEntryHelper.suggest_cleaning_fee(
                data['bedrooms'], data['bathrooms']
            )
        
        if data.get('address'):
            response['suggested_name'] = ManualEntryHelper.suggest_property_name(
                data['address'], data.get('property_type', '')
            )
        
        return jsonify(response)
        
    except Exception as e:
        logging.error(f"Error in property validation endpoint: {str(e)}")
        return jsonify({
            'valid': False,
            'error': f'Validation failed: {str(e)}'
        }), 500 