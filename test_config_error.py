#!/usr/bin/env python3
"""
Test to reproduce configuration page access issue
"""

from app import create_app, db
from app.models import User
from flask import url_for
import sys

app = create_app()

with app.app_context():
    # Get an admin user
    admin = User.query.filter_by(email='admin@landlord.com').first()
    if not admin:
        print("Admin user not found")
        sys.exit(1)
    
    print(f"Testing with admin user: {admin.email}")
    
    # Create test client
    client = app.test_client()
    
    with client:
        # Try to directly access the configuration page (should redirect to login)
        print("\n1. Trying direct access to /admin/configuration/...")
        response = client.get('/admin/configuration/', follow_redirects=False)
        print(f"   Status: {response.status_code}")
        if response.status_code == 302:
            print(f"   Redirected to: {response.location}")
        
        # Get login page
        print("\n2. Getting login page...")
        response = client.get('/auth/login')
        print(f"   Status: {response.status_code}")
        
        # Extract CSRF token
        import re
        csrf_match = re.search(r'name="csrf_token".*?value="([^"]+)"', response.data.decode())
        if not csrf_match:
            print("   ERROR: Could not find CSRF token")
            sys.exit(1)
        
        csrf_token = csrf_match.group(1)
        print(f"   CSRF token obtained: {csrf_token[:20]}...")
        
        # Try to login
        print("\n3. Attempting login...")
        login_data = {
            'email': admin.email,
            'password': 'admin123',  # Try default password
            'csrf_token': csrf_token,
            'submit': 'Sign In'
        }
        
        response = client.post('/auth/login', data=login_data, follow_redirects=False)
        print(f"   Status: {response.status_code}")
        if response.status_code == 302:
            print(f"   Redirected to: {response.location}")
        
        # Now try to access configuration page
        print("\n4. Accessing /admin/configuration/ after login...")
        response = client.get('/admin/configuration/', follow_redirects=False)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✅ Configuration page loaded successfully!")
            # Check content
            content = response.data.decode()
            if 'Configuration Management' in content:
                print("   ✅ Page contains 'Configuration Management'")
            else:
                print("   ⚠️ Page loaded but doesn't contain expected content")
                print("   First 500 chars of response:")
                print(content[:500])
        elif response.status_code == 302:
            print(f"   ⚠️ Still redirecting to: {response.location}")
            print("   This means authentication failed or user is not admin")
        else:
            print(f"   ❌ Unexpected status code: {response.status_code}")
            
            # Check if there's an error in the response
            try:
                content = response.data.decode()
                if 'error' in content.lower() or 'exception' in content.lower():
                    print("\n   ERROR FOUND IN RESPONSE:")
                    # Extract error message
                    import re
                    error_match = re.search(r'<title>(.*?)</title>', content)
                    if error_match:
                        print(f"   Title: {error_match.group(1)}")
                    
                    # Look for exception details
                    if 'AttributeError' in content:
                        print("   AttributeError detected!")
                        error_details = re.search(r'AttributeError.*?<', content)
                        if error_details:
                            print(f"   {error_details.group(0)[:-1]}")
            except:
                pass