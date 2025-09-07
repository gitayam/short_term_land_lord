"""
Property Data Service
Integrates enhanced Zillow scraper with property creation workflow.
Provides seamless property data collection for the Short Term Landlord application.
"""

import logging
from typing import Dict, Optional, Union

from flask import current_app

from app.utils.zillow_scraper_v2 import PropertyDataService as BasePropertyDataService
from app.models import Property, db


class PropertyDataIntegrationService:
    """
    Service that integrates property data collection with the application's property management system.
    """
    
    def __init__(self):
        self.data_service = BasePropertyDataService()
    
    def create_property_from_address(self, address_or_url: str, owner_id: int, **additional_data) -> Property:
        """
        Create a new property by fetching data from address/URL and saving to database.
        
        Args:
            address_or_url: Property address or Zillow URL
            owner_id: ID of the property owner
            **additional_data: Additional property data to override or supplement scraped data
            
        Returns:
            Property: Created property object
            
        Raises:
            RuntimeError: If property data cannot be fetched from any source
            ValueError: If required fields are missing
        """
        try:
            # Fetch property data from external sources
            property_data = self.data_service.get_property_data(address_or_url)
            
            # Merge with additional data (user input takes precedence)
            merged_data = {**property_data, **additional_data}
            
            # Create property object
            property_obj = self._create_property_from_data(merged_data, owner_id)
            
            # Save to database
            db.session.add(property_obj)
            db.session.commit()
            
            logging.info(f"Successfully created property {property_obj.id} from address: {address_or_url}")
            return property_obj
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Failed to create property from address {address_or_url}: {str(e)}")
            raise
    
    def update_property_from_zillow(self, property_id: int, zillow_url: str) -> Property:
        """
        Update an existing property with data from Zillow.
        
        Args:
            property_id: ID of existing property
            zillow_url: Zillow URL for the property
            
        Returns:
            Property: Updated property object
        """
        property_obj = Property.query.get_or_404(property_id)
        
        try:
            # Fetch updated data
            property_data = self.data_service.get_property_data(zillow_url)
            
            # Update property fields (preserve existing data where scraper returns None)
            self._update_property_fields(property_obj, property_data)
            
            db.session.commit()
            
            logging.info(f"Successfully updated property {property_id} from Zillow")
            return property_obj
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Failed to update property {property_id} from Zillow: {str(e)}")
            raise
    
    def get_property_suggestions(self, partial_address: str) -> Dict[str, Union[str, list]]:
        """
        Get property suggestions and preview data for a partial address.
        
        Args:
            partial_address: Partial address or search query
            
        Returns:
            Dict containing property suggestions and preview data
        """
        try:
            # For now, just try to get data for the address
            # In the future, this could return multiple suggestions
            property_data = self.data_service.get_property_data(partial_address)
            
            return {
                'suggestions': [property_data],
                'preview': property_data,
                'success': True
            }
            
        except Exception as e:
            logging.warning(f"Could not get suggestions for address {partial_address}: {str(e)}")
            return {
                'suggestions': [],
                'preview': None,
                'success': False,
                'error': str(e)
            }
    
    def _create_property_from_data(self, data: Dict, owner_id: int) -> Property:
        """Create a Property object from scraped data."""
        
        # Extract and clean address components
        address = data.get('address', '')
        address_parts = self._parse_address(address)
        
        # Create property with all available data
        property_obj = Property(
            owner_id=owner_id,
            name=data.get('name') or self._generate_property_name(address),
            address=address,
            street=address_parts.get('street', ''),
            city=address_parts.get('city', ''),
            state=address_parts.get('state', ''),
            zip_code=address_parts.get('zip_code', ''),
            
            # Property details from scraper
            bedrooms=data.get('bedrooms'),
            bathrooms=data.get('bathrooms'), 
            square_feet=data.get('square_feet'),
            year_built=data.get('year_built'),
            property_type=data.get('property_type', 'Unknown'),
            
            # Financial data
            estimated_value=data.get('price'),
            
            # Description and images
            description=data.get('description', ''),
            
            # Default values for required fields
            is_active=True,
            max_guests=data.get('max_guests', 4),  # Default based on bedrooms
            cleaning_fee=data.get('cleaning_fee', 50.0),  # Default cleaning fee
        )
        
        # Set max guests based on bedrooms if not provided
        if not data.get('max_guests') and data.get('bedrooms'):
            property_obj.max_guests = max(2, int(data.get('bedrooms')) * 2)
        
        return property_obj
    
    def _update_property_fields(self, property_obj: Property, data: Dict) -> None:
        """Update property fields with new data, preserving existing values where appropriate."""
        
        # Update fields only if new data is available and different
        update_fields = {
            'address': data.get('address'),
            'bedrooms': data.get('bedrooms'),
            'bathrooms': data.get('bathrooms'),
            'square_feet': data.get('square_feet'),
            'year_built': data.get('year_built'),
            'property_type': data.get('property_type'),
            'estimated_value': data.get('price'),
        }
        
        for field, value in update_fields.items():
            if value is not None and hasattr(property_obj, field):
                current_value = getattr(property_obj, field)
                if current_value != value:
                    setattr(property_obj, field, value)
                    logging.info(f"Updated {field}: {current_value} -> {value}")
    
    def _parse_address(self, address: str) -> Dict[str, str]:
        """Parse address string into components."""
        if not address:
            return {}
        
        # Simple address parsing - could be enhanced with a proper address parser
        parts = address.split(',')
        result = {'street': ''}
        
        if len(parts) >= 1:
            result['street'] = parts[0].strip()
        
        if len(parts) >= 2:
            result['city'] = parts[1].strip()
        
        if len(parts) >= 3:
            # Last part usually contains state and zip
            state_zip = parts[-1].strip().split()
            if len(state_zip) >= 1:
                result['state'] = state_zip[0]
            if len(state_zip) >= 2:
                result['zip_code'] = state_zip[1]
        
        return result
    
    def _generate_property_name(self, address: str) -> str:
        """Generate a property name from address."""
        if not address:
            return "Unnamed Property"
        
        # Extract street address for property name
        parts = address.split(',')
        if parts:
            return f"Property at {parts[0].strip()}"
        
        return "Property from Zillow"


# Flask integration helper functions
def integrate_with_property_routes():
    """
    Integration helper for property routes.
    This should be called from property routes to enable enhanced data collection.
    """
    from flask import request, jsonify
    
    service = PropertyDataIntegrationService()
    
    def handle_zillow_data_request():
        """Handle AJAX request for Zillow data."""
        address_or_url = request.json.get('address_or_url', '')
        
        if not address_or_url:
            return jsonify({'success': False, 'error': 'Address or URL required'})
        
        try:
            suggestions = service.get_property_suggestions(address_or_url)
            return jsonify(suggestions)
            
        except Exception as e:
            return jsonify({
                'success': False, 
                'error': f'Failed to fetch property data: {str(e)}'
            })
    
    return handle_zillow_data_request


# Test function
def test_property_data_service():
    """Test the property data service integration."""
    service = PropertyDataIntegrationService()
    
    # Test address from user's issue  
    test_address = "824 Carol St, Fayetteville, NC 28303"
    
    try:
        suggestions = service.get_property_suggestions(test_address)
        print("Property data service test results:")
        print(f"Success: {suggestions['success']}")
        
        if suggestions['success']:
            preview = suggestions['preview']
            print(f"Address: {preview.get('address')}")
            print(f"Price: ${preview.get('price'):,}" if preview.get('price') else "Price: Not available")
            print(f"Bedrooms: {preview.get('bedrooms')}")
            print(f"Bathrooms: {preview.get('bathrooms')}")
            print(f"Square Feet: {preview.get('square_feet')}")
        else:
            print(f"Error: {suggestions.get('error')}")
            
        return suggestions
        
    except Exception as e:
        print(f"Test failed: {e}")
        return None


if __name__ == "__main__":
    test_property_data_service()