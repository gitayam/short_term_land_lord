#!/usr/bin/env python3
"""
Test script for the Zillow scraper V2 locally
"""

import sys
import os
sys.path.append('.')

def test_zillow_scraper():
    """Test the new Zillow scraper locally."""
    print("🧪 Testing Zillow Scraper V2 - Local Test")
    print("=" * 50)
    
    try:
        # Set environment for local testing
        os.environ['DATABASE_URL'] = 'sqlite:///local_development.db'
        os.environ['FLASK_ENV'] = 'development'
        
        from app.services.property_data_service import PropertyDataIntegrationService
        
        # Initialize the service
        service = PropertyDataIntegrationService()
        print("✅ Property data service initialized successfully")
        
        # Test the problematic URL from user's issue
        test_url = "https://www.zillow.com/homedetails/824-Carol-St-Fayetteville-NC-28303/53646204_zpid/"
        
        print(f"🎯 Testing URL: {test_url}")
        print()
        
        # Test the service
        print("📡 Testing property data service...")
        result = service.get_property_suggestions(test_url)
        
        if result['success']:
            print("✅ SUCCESS: Property data retrieved!")
            print_property_data(result['preview'])
            return True
        else:
            print(f"❌ FAILED: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False

def print_property_data(data):
    """Print property data in a nice format."""
    if not data:
        print("No data to display")
        return
        
    print()
    print("🏠 PROPERTY DATA EXTRACTED:")
    print("-" * 30)
    for key, value in data.items():
        if value:
            print(f"  {key.replace('_', ' ').title()}: {value}")
    print()

if __name__ == "__main__":
    success = test_zillow_scraper()
    if success:
        print("🎉 Local Zillow scraper test PASSED!")
        sys.exit(0)
    else:
        print("💥 Local Zillow scraper test FAILED!")
        sys.exit(1)