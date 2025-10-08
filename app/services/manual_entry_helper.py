"""
Manual Entry Helper Service
Provides intelligent form pre-filling and validation for manual property entry.
Used when automated data sources (RentCast, scraping) fail.
"""

import re
from typing import Dict, Optional, Tuple


class ManualEntryHelper:
    """
    Helper service for manual property data entry.
    Provides address parsing, validation, and smart defaults.
    """
    
    @staticmethod
    def parse_address(address_input: str) -> Dict[str, str]:
        """
        Parse address input into components for form pre-filling.
        
        Args:
            address_input: Raw address string
            
        Returns:
            Dict with parsed address components
        """
        if not address_input or not address_input.strip():
            return {}
        
        address = address_input.strip()
        result = {'address': address}
        
        # Remove Zillow URL if present and try to extract address
        if 'zillow.com' in address.lower():
            # Extract address from Zillow URL path
            zillow_match = re.search(r'/([^/]*-[A-Z]{2}-\d{5})/', address)
            if zillow_match:
                # Convert URL format back to address
                url_part = zillow_match.group(1)
                # Replace hyphens with spaces except for state-zip
                parts = url_part.split('-')
                if len(parts) >= 3:
                    # Last part is ZIP, second to last is state
                    zip_code = parts[-1]
                    state = parts[-2]
                    street_city = '-'.join(parts[:-2]).replace('-', ' ')
                    result['address'] = f"{street_city}, {state} {zip_code}"
                    result['state'] = state
                    result['zip_code'] = zip_code
        
        # Try to parse standard address format
        if ',' in result['address']:
            parts = result['address'].split(',')
            
            # Extract ZIP code from last part
            if len(parts) >= 2:
                last_part = parts[-1].strip()
                zip_match = re.search(r'(\d{5}(?:-\d{4})?)', last_part)
                if zip_match:
                    result['zip_code'] = zip_match.group(1)
                    # Extract state (usually 2 letters before ZIP)
                    state_match = re.search(r'([A-Z]{2})\s+\d{5}', last_part)
                    if state_match:
                        result['state'] = state_match.group(1)
                
            # City is usually second-to-last part
            if len(parts) >= 3:
                result['city'] = parts[-2].strip()
            elif len(parts) == 2:
                # Remove state/ZIP from city part
                city_part = parts[-1].strip()
                city_part = re.sub(r'\s+[A-Z]{2}\s+\d{5}.*', '', city_part)
                if city_part:
                    result['city'] = city_part
        
        return result
    
    @staticmethod
    def suggest_property_name(address: str, property_type: str = "") -> str:
        """
        Suggest a property name based on address.
        
        Args:
            address: Property address
            property_type: Optional property type
            
        Returns:
            Suggested property name
        """
        if not address:
            return "New Property"
        
        # Extract street address (first part before comma)
        if ',' in address:
            street_part = address.split(',')[0].strip()
        else:
            street_part = address.strip()
        
        # Get first few words for name
        words = street_part.split()[:3]  # Take first 3 words max
        street_name = ' '.join(words)
        
        if property_type:
            return f"{property_type} at {street_name}"
        else:
            return f"Property at {street_name}"
    
    @staticmethod
    def estimate_max_guests(bedrooms: Optional[int]) -> int:
        """
        Estimate maximum guests based on bedrooms.
        
        Args:
            bedrooms: Number of bedrooms
            
        Returns:
            Estimated maximum guests
        """
        if not bedrooms or bedrooms < 1:
            return 2  # Default minimum
        
        # Standard estimation: 2 guests per bedroom, minimum 2
        return max(2, bedrooms * 2)
    
    @staticmethod
    def suggest_cleaning_fee(bedrooms: Optional[int], bathrooms: Optional[int]) -> float:
        """
        Suggest cleaning fee based on property size.
        
        Args:
            bedrooms: Number of bedrooms
            bathrooms: Number of bathrooms
            
        Returns:
            Suggested cleaning fee
        """
        base_fee = 50.0  # Base cleaning fee
        
        # Add $15 per bedroom
        if bedrooms and bedrooms > 1:
            base_fee += (bedrooms - 1) * 15
        
        # Add $10 per bathroom
        if bathrooms and bathrooms > 1:
            base_fee += (bathrooms - 1) * 10
        
        # Round to nearest $5
        return round(base_fee / 5) * 5
    
    @staticmethod
    def get_property_type_suggestions() -> list:
        """Get list of common property types for dropdown."""
        return [
            "House",
            "Apartment",
            "Condo", 
            "Townhouse",
            "Duplex",
            "Studio",
            "Cabin",
            "Villa",
            "Loft",
            "Other"
        ]
    
    @staticmethod
    def validate_required_fields(data: Dict) -> Tuple[bool, list]:
        """
        Validate that required fields are present for property creation.
        
        Args:
            data: Property data dictionary
            
        Returns:
            Tuple of (is_valid, list_of_missing_fields)
        """
        required_fields = ['address', 'bedrooms', 'bathrooms']
        missing_fields = []
        
        for field in required_fields:
            if not data.get(field):
                missing_fields.append(field.replace('_', ' ').title())
        
        return len(missing_fields) == 0, missing_fields
    
    @staticmethod
    def get_form_help_text() -> Dict[str, str]:
        """Get help text for form fields."""
        return {
            'address': 'Enter the full street address including city, state, and ZIP code',
            'bedrooms': 'Number of bedrooms available to guests',
            'bathrooms': 'Number of bathrooms (use 0.5 for half baths)',
            'square_feet': 'Total livable square footage of the property',
            'year_built': 'Year the property was constructed',
            'property_type': 'Type of property (house, apartment, condo, etc.)',
            'max_guests': 'Maximum number of guests allowed',
            'cleaning_fee': 'One-time cleaning fee charged to guests'
        }


def test_manual_entry_helper():
    """Test the manual entry helper functions."""
    helper = ManualEntryHelper()
    
    print("🛠️  Testing Manual Entry Helper")
    print("=" * 35)
    
    # Test address parsing
    test_addresses = [
        "824 Carol St, Fayetteville, NC 28303",
        "https://www.zillow.com/homedetails/824-Carol-St-Fayetteville-NC-28303/53646204_zpid/",
        "123 Main Street, Austin, TX 78701"
    ]
    
    for address in test_addresses:
        print(f"\nTesting: {address}")
        parsed = helper.parse_address(address)
        for key, value in parsed.items():
            if value:
                print(f"  {key}: {value}")
    
    # Test suggestions
    print(f"\nProperty name suggestion: {helper.suggest_property_name('824 Carol St', 'House')}")
    print(f"Max guests for 3 bedrooms: {helper.estimate_max_guests(3)}")
    print(f"Cleaning fee for 2BR/2BA: ${helper.suggest_cleaning_fee(2, 2)}")


if __name__ == "__main__":
    test_manual_entry_helper()