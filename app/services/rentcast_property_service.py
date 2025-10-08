"""
RentCast Property Data Service
Replaces Zillow scraping with reliable RentCast API integration.
Provides property data for short-term rental management.
"""

import os
import logging
import requests
from typing import Dict, Optional, Union
from urllib.parse import quote_plus

logger = logging.getLogger(__name__)


class RentCastPropertyService:
    """
    Service for fetching property data from RentCast API.
    More reliable and legal alternative to Zillow scraping.
    """
    
    def __init__(self):
        self.api_key = os.environ.get('RENTCAST_API_KEY')
        self.base_url = 'https://api.rentcast.io/v1'
        self.session = requests.Session()
        
        if not self.api_key:
            logger.warning("RENTCAST_API_KEY not found. Property data fetching will be limited.")
    
    def get_property_data(self, address: str) -> Dict[str, Union[str, int, float]]:
        """
        Get comprehensive property data from RentCast API.
        
        Args:
            address: Property address (e.g., "123 Main St, City, State ZIP")
            
        Returns:
            Dict containing property details or empty dict if not found
        """
        if not self.api_key:
            logger.error("RentCast API key not configured")
            return {}
        
        try:
            # Clean and format address
            clean_address = self._clean_address(address)
            logger.info(f"Fetching property data for: {clean_address}")
            
            # Get property details
            property_data = self._fetch_property_details(clean_address)
            
            if property_data:
                # Get rental estimate if available
                rental_data = self._fetch_rental_estimate(clean_address)
                if rental_data:
                    property_data.update(rental_data)
                
                # Transform to standard format
                return self._transform_to_standard_format(property_data)
            
            return {}
            
        except Exception as e:
            logger.error(f"Error fetching property data from RentCast: {e}")
            return {}
    
    def _clean_address(self, address: str) -> str:
        """Clean and normalize address for API call."""
        # Remove Zillow URL if provided and extract address
        if 'zillow.com' in address.lower():
            # Extract address from URL path if possible
            # For now, return as-is and let user provide proper address
            logger.info("Zillow URL detected - user should provide street address")
            return address
        
        # Basic address cleaning
        address = address.strip()
        # Remove extra spaces
        address = ' '.join(address.split())
        return address
    
    def _fetch_property_details(self, address: str) -> Optional[Dict]:
        """Fetch property details from RentCast API."""
        try:
            url = f"{self.base_url}/avm/sale-price"
            params = {
                'address': address,
                'propertyType': 'Single Family'  # Default, API will correct if needed
            }
            headers = {
                'X-Api-Key': self.api_key,
                'accept': 'application/json'
            }
            
            response = self.session.get(url, params=params, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Successfully fetched property details from RentCast")
                return data
            elif response.status_code == 404:
                logger.warning(f"Property not found in RentCast database: {address}")
                return None
            else:
                logger.error(f"RentCast API error {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Exception calling RentCast property API: {e}")
            return None
    
    def _fetch_rental_estimate(self, address: str) -> Optional[Dict]:
        """Fetch rental estimate from RentCast API."""
        try:
            url = f"{self.base_url}/avm/rent/long-term"
            params = {
                'address': address,
                'propertyType': 'Single Family'
            }
            headers = {
                'X-Api-Key': self.api_key,
                'accept': 'application/json'
            }
            
            response = self.session.get(url, params=params, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Successfully fetched rental estimate from RentCast")
                return data
            else:
                logger.warning(f"Could not fetch rental estimate: {response.status_code}")
                return None
                
        except Exception as e:
            logger.warning(f"Exception calling RentCast rental API: {e}")
            return None
    
    def _transform_to_standard_format(self, api_data: Dict) -> Dict[str, Union[str, int, float]]:
        """Transform RentCast API response to standard property data format."""
        try:
            # Extract basic property info
            result = {}
            
            # Address information
            if 'address' in api_data:
                addr = api_data['address']
                result['address'] = f"{addr.get('line', '')} {addr.get('city', '')} {addr.get('state', '')} {addr.get('zipCode', '')}".strip()
                result['city'] = addr.get('city', '')
                result['state'] = addr.get('state', '')
                result['zip_code'] = addr.get('zipCode', '')
            
            # Property details
            if 'property' in api_data:
                prop = api_data['property']
                result['bedrooms'] = prop.get('bedrooms')
                result['bathrooms'] = prop.get('bathrooms')
                result['square_feet'] = prop.get('squareFootage')
                result['year_built'] = prop.get('yearBuilt')
                result['property_type'] = prop.get('propertyType', '').replace('_', ' ').title()
            
            # Pricing information
            if 'price' in api_data:
                result['estimated_value'] = api_data['price']
            elif 'salePrice' in api_data:
                result['estimated_value'] = api_data['salePrice']
            
            # Rental estimate
            if 'rent' in api_data:
                result['estimated_rent'] = api_data['rent']
            elif 'rentEstimate' in api_data:
                result['estimated_rent'] = api_data['rentEstimate']
            
            # Generate property name
            if result.get('address'):
                # Extract street address for name
                addr_parts = result['address'].split(' ')
                if len(addr_parts) >= 2:
                    result['name'] = f"Property at {addr_parts[0]} {addr_parts[1]}"
                else:
                    result['name'] = f"Property at {result['address'][:50]}"
            
            # Add description
            details = []
            if result.get('bedrooms'):
                details.append(f"{result['bedrooms']} bed")
            if result.get('bathrooms'):
                details.append(f"{result['bathrooms']} bath")
            if result.get('square_feet'):
                details.append(f"{result['square_feet']:,} sq ft")
            if result.get('year_built'):
                details.append(f"built {result['year_built']}")
            
            if details:
                result['description'] = f"{result.get('property_type', 'Property')} - {', '.join(details)}"
            
            logger.info(f"Transformed RentCast data: {len(result)} fields populated")
            return result
            
        except Exception as e:
            logger.error(f"Error transforming RentCast data: {e}")
            return {}


def test_rentcast_service():
    """Test function for RentCast service."""
    service = RentCastPropertyService()
    
    # Test with the problematic address
    test_address = "824 Carol St, Fayetteville, NC 28303"
    
    print("🏠 Testing RentCast Property Service")
    print(f"Address: {test_address}")
    print("-" * 40)
    
    result = service.get_property_data(test_address)
    
    if result:
        print("✅ SUCCESS! Property data found:")
        for key, value in result.items():
            if value:
                print(f"  {key}: {value}")
    else:
        print("❌ No property data found")
        print("💡 Make sure RENTCAST_API_KEY is set in environment")


if __name__ == "__main__":
    test_rentcast_service()