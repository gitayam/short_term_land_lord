#!/usr/bin/env python3

from app import create_app, db
from app.models import User, UserRoles, ServiceType
from config import TestConfig
from flask import current_app

def test_sms_in_context():
    app = create_app(TestConfig)
    with app.app_context():
        with app.test_request_context():
            db.create_all()
            
            # Test SMS function within Flask app and request context
            from app.utils.sms import send_sms
            
            print("Testing SMS function within Flask app and request context...")
            print(f"Twilio Account SID: {current_app.config.get('TWILIO_ACCOUNT_SID', 'NOT SET')}")
            print(f"Twilio Auth Token: {current_app.config.get('TWILIO_AUTH_TOKEN', 'NOT SET')[:10]}..." if current_app.config.get('TWILIO_AUTH_TOKEN') else 'NOT SET')
            print(f"Twilio Phone Number: {current_app.config.get('TWILIO_PHONE_NUMBER', 'NOT SET')}")
            
            success, error = send_sms('+1234567890', 'Test message from Flask app context')
            print(f"SMS result: success={success}, error='{error}'")
            
            if success:
                print("✓ SMS sent successfully!")
            elif "SMS disabled" in error:
                print("✓ SMS gracefully disabled")
            else:
                print(f"✗ SMS error: {error}")
            
            print("SMS test completed!")

if __name__ == '__main__':
    test_sms_in_context() 