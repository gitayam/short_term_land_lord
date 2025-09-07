#!/usr/bin/env python3

from app import create_app, db
from app.models import User, UserRoles, ServiceType
from config import TestConfig

def test_workforce_invite():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        
        # Create a test user for invitation
        test_user = User(
            first_name='Test',
            last_name='Worker',
            email='testworker@example.com',
            role=UserRoles.SERVICE_STAFF.value
        )
        test_user.set_password('test_password')
        
        # Test SMS function without Twilio credentials
        from app.utils.sms import send_sms
        
        print("Testing SMS function without Twilio credentials...")
        success, error = send_sms('+1234567890', 'Test message')
        print(f"SMS result: success={success}, error='{error}'")
        
        if "SMS disabled" in error:
            print("✓ SMS gracefully disabled when credentials missing")
        else:
            print("✗ SMS error handling not working correctly")
        
        print("Workforce invitation test completed!")

if __name__ == '__main__':
    test_workforce_invite() 