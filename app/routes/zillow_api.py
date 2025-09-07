"""
Zillow API Routes
Enhanced property data collection endpoints for the Short Term Landlord application.
"""

import logging
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user

from app.services.property_data_service import PropertyDataIntegrationService
from app.models import Property, db, UserRoles

# Create blueprint
zillow_bp = Blueprint('zillow', __name__, url_prefix='/api/zillow')

# Initialize service
property_data_service = PropertyDataIntegrationService()


@zillow_bp.route('/property-data', methods=['POST'])
@login_required
def get_property_data():
    """
    Get property data from address or Zillow URL.
    
    POST /api/zillow/property-data
    {
        "address_or_url": "824 Carol St, Fayetteville, NC 28303"
    }
    
    Returns property details for populating the property creation form.
    """
    try:
        data = request.get_json()
        if not data or not data.get('address_or_url'):
            return jsonify({
                'success': False,
                'error': 'Address or URL is required'
            }), 400
        
        address_or_url = data['address_or_url'].strip()
        
        # Log the request
        current_app.logger.info(f"User {current_user.id} requesting property data for: {address_or_url}")
        
        # Get property suggestions/data
        result = property_data_service.get_property_suggestions(address_or_url)
        
        if result['success']:
            return jsonify({
                'success': True,
                'data': result['preview'],
                'message': 'Property data retrieved successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Failed to fetch property data'),
                'message': 'Could not retrieve property data. Please enter details manually.'
            }), 422
            
    except Exception as e:
        current_app.logger.error(f"Error in get_property_data: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'message': 'Something went wrong. Please try again.'
        }), 500


@zillow_bp.route('/create-property', methods=['POST'])
@login_required
def create_property_from_data():
    """
    Create a new property using scraped data.
    
    POST /api/zillow/create-property
    {
        "address_or_url": "824 Carol St, Fayetteville, NC 28303",
        "name": "Optional custom name",
        "cleaning_fee": 75.00,
        "max_guests": 6
    }
    
    Creates property with scraped data + user overrides.
    """
    try:
        # Check permissions
        if current_user.role not in [UserRoles.PROPERTY_OWNER.value, UserRoles.ADMIN.value]:
            return jsonify({
                'success': False,
                'error': 'Permission denied'
            }), 403
        
        data = request.get_json()
        if not data or not data.get('address_or_url'):
            return jsonify({
                'success': False,
                'error': 'Address or URL is required'
            }), 400
        
        address_or_url = data['address_or_url'].strip()
        
        # Extract additional data for property creation
        additional_data = {}
        for key in ['name', 'cleaning_fee', 'max_guests', 'description']:
            if key in data and data[key]:
                additional_data[key] = data[key]
        
        # Create property
        property_obj = property_data_service.create_property_from_address(
            address_or_url=address_or_url,
            owner_id=current_user.id,
            **additional_data
        )
        
        current_app.logger.info(f"User {current_user.id} created property {property_obj.id} from: {address_or_url}")
        
        return jsonify({
            'success': True,
            'property_id': property_obj.id,
            'message': f'Property "{property_obj.name}" created successfully',
            'data': {
                'id': property_obj.id,
                'name': property_obj.name,
                'address': property_obj.address,
                'bedrooms': property_obj.bedrooms,
                'bathrooms': property_obj.bathrooms,
                'square_feet': property_obj.square_feet
            }
        })
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Invalid property data. Please check the address and try again.'
        }), 422
        
    except Exception as e:
        current_app.logger.error(f"Error in create_property_from_data: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to create property',
            'message': 'Something went wrong. Please try again.'
        }), 500


@zillow_bp.route('/update-property/<int:property_id>', methods=['PUT'])
@login_required
def update_property_from_zillow(property_id):
    """
    Update existing property with Zillow data.
    
    PUT /api/zillow/update-property/123
    {
        "zillow_url": "https://www.zillow.com/homedetails/..."
    }
    """
    try:
        # Get property and check ownership
        property_obj = Property.query.get_or_404(property_id)
        
        # Check permissions
        if (current_user.role != UserRoles.ADMIN.value and 
            property_obj.owner_id != current_user.id):
            return jsonify({
                'success': False,
                'error': 'Permission denied'
            }), 403
        
        data = request.get_json()
        if not data or not data.get('zillow_url'):
            return jsonify({
                'success': False,
                'error': 'Zillow URL is required'
            }), 400
        
        # Update property
        updated_property = property_data_service.update_property_from_zillow(
            property_id=property_id,
            zillow_url=data['zillow_url']
        )
        
        return jsonify({
            'success': True,
            'message': f'Property "{updated_property.name}" updated successfully',
            'data': {
                'id': updated_property.id,
                'name': updated_property.name,
                'address': updated_property.address,
                'bedrooms': updated_property.bedrooms,
                'bathrooms': updated_property.bathrooms,
                'square_feet': updated_property.square_feet,
                'estimated_value': updated_property.estimated_value
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error in update_property_from_zillow: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to update property from Zillow'
        }), 500


@zillow_bp.route('/test-scraper', methods=['GET'])
@login_required
def test_scraper():
    """
    Test endpoint for the Zillow scraper.
    Only available to admin users for debugging.
    
    GET /api/zillow/test-scraper?url=https://www.zillow.com/homedetails/...
    """
    if current_user.role != UserRoles.ADMIN.value:
        return jsonify({'error': 'Admin access required'}), 403
    
    test_url = request.args.get('url') or request.args.get('address')
    if not test_url:
        # Use the failing URL from the user's issue as default
        test_url = "https://www.zillow.com/homedetails/824-Carol-St-Fayetteville-NC-28303/53646204_zpid/"
    
    try:
        from app.utils.zillow_scraper_v2 import ZillowScraperV2
        
        scraper = ZillowScraperV2()
        result = scraper.fetch_property_details(test_url)
        
        return jsonify({
            'success': True,
            'test_url': test_url,
            'result': result,
            'message': 'Scraper test completed successfully'
        })
        
    except Exception as e:
        current_app.logger.error(f"Scraper test failed: {str(e)}")
        return jsonify({
            'success': False,
            'test_url': test_url,
            'error': str(e),
            'message': 'Scraper test failed'
        })


# Error handlers
@zillow_bp.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'Endpoint not found'
    }), 404


@zillow_bp.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500