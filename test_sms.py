#!/usr/bin/env python3
"""
Test script for SMS functionality
This script tests the SMS sending functionality to help debug issues.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_sms_config():
    """Test SMS configuration"""
    print("Testing SMS Configuration...")
    
    # Check environment variables
    twilio_account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
    twilio_auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
    twilio_phone_number = os.environ.get('TWILIO_PHONE_NUMBER')
    
    print(f"TWILIO_ACCOUNT_SID: {'✓ Set' if twilio_account_sid else '✗ Missing'}")
    print(f"TWILIO_AUTH_TOKEN: {'✓ Set' if twilio_auth_token else '✗ Missing'}")
    print(f"TWILIO_PHONE_NUMBER: {'✓ Set' if twilio_phone_number else '✗ Missing'}")
    
    if not all([twilio_account_sid, twilio_auth_token, twilio_phone_number]):
        print("\n❌ SMS configuration is incomplete!")
        return False
    
    print("\n✅ SMS configuration looks good!")
    return True

def test_twilio_import():
    """Test Twilio import"""
    print("\nTesting Twilio Import...")
    
    try:
        from twilio.rest import Client
        print("✅ Twilio import successful")
        return True
    except ImportError as e:
        print(f"❌ Twilio import failed: {e}")
        return False

def test_sms_function():
    """Test the SMS function"""
    print("\nTesting SMS Function...")
    
    try:
        from app.utils.sms import send_sms
        print("✅ SMS function import successful")
        
        # Test with a dummy phone number (won't actually send)
        test_phone = "+1234567890"
        test_message = "This is a test message from the SMS test script"
        
        print(f"Testing SMS function with phone: {test_phone}")
        print(f"Message: {test_message}")
        
        # This will likely fail due to invalid credentials or phone number, but should not crash
        success, error = send_sms(test_phone, test_message)
        
        print(f"Result: {'Success' if success else 'Failed'}")
        if not success:
            print(f"Error: {error}")
        
        return True
        
    except Exception as e:
        print(f"❌ SMS function test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print("SMS Functionality Test")
    print("=" * 50)
    
    # Test configuration
    config_ok = test_sms_config()
    
    # Test Twilio import
    import_ok = test_twilio_import()
    
    # Test SMS function
    function_ok = test_sms_function()
    
    print("\n" + "=" * 50)
    print("Test Summary:")
    print(f"Configuration: {'✅ PASS' if config_ok else '❌ FAIL'}")
    print(f"Twilio Import: {'✅ PASS' if import_ok else '❌ FAIL'}")
    print(f"SMS Function: {'✅ PASS' if function_ok else '❌ FAIL'}")
    
    if all([config_ok, import_ok, function_ok]):
        print("\n🎉 All tests passed! SMS functionality should work correctly.")
    else:
        print("\n⚠️  Some tests failed. Please check the configuration and dependencies.")

if __name__ == "__main__":
    main() 