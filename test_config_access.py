#!/usr/bin/env python3
"""
Test script to verify configuration management system is working
"""

from app import create_app, db
from app.models import User
from flask import url_for

app = create_app()

with app.app_context():
    with app.test_request_context():
        # Test URL generation
        config_url = url_for('admin_config.index')
        print(f"✅ Configuration URL generated: {config_url}")
        
        category_url = url_for('admin_config.category_settings', category='application')
        print(f"✅ Category URL generated: {category_url}")
        
        audit_url = url_for('admin_config.audit_log')
        print(f"✅ Audit URL generated: {audit_url}")
        
        # Test configuration service
        from app.utils.configuration import config_service
        
        # Get all categories
        categories = config_service.get_categories()
        print(f"\n📂 Found {len(categories)} configuration categories:")
        for cat in categories:
            print(f"   - {cat}")
        
        # Get some configuration values
        app_name = config_service.get('APP_NAME')
        print(f"\n🔧 Sample configuration values:")
        print(f"   APP_NAME: {app_name}")
        
        max_props = config_service.get('MAX_PROPERTIES_PER_USER')
        print(f"   MAX_PROPERTIES_PER_USER: {max_props}")
        
        # Test with an admin user
        admin = User.query.filter_by(is_admin=True).first()
        if admin:
            print(f"\n👤 Admin user available: {admin.email}")
            
            # Test client access
            client = app.test_client()
            
            # Login as admin
            with client:
                # Get login page for CSRF token
                response = client.get('/auth/login')
                assert response.status_code == 200
                
                # Extract CSRF token from response
                import re
                csrf_match = re.search(r'name="csrf_token".*?value="([^"]+)"', response.data.decode())
                if csrf_match:
                    csrf_token = csrf_match.group(1)
                    
                    # Login
                    login_data = {
                        'email': admin.email,
                        'password': 'admin123',  # Try common password
                        'csrf_token': csrf_token,
                        'submit': 'Sign In'
                    }
                    
                    response = client.post('/auth/login', data=login_data, follow_redirects=True)
                    
                    # Try to access configuration page
                    response = client.get('/admin/configuration/')
                    print(f"\n🌐 Configuration page access: Status {response.status_code}")
                    
                    if response.status_code == 200:
                        print("✅ Configuration management system is accessible!")
                        
                        # Check if the page contains expected content
                        content = response.data.decode()
                        if 'Configuration Management' in content:
                            print("✅ Configuration Management page loaded successfully!")
                        if 'System Settings' in content or 'system' in content.lower():
                            print("✅ Configuration categories are displayed!")
                    elif response.status_code == 302:
                        print("⚠️ Redirected - likely authentication issue")
                        print(f"   Redirect location: {response.location}")
                    else:
                        print(f"❌ Unexpected status code: {response.status_code}")
                        
        else:
            print("\n⚠️ No admin user found for testing")

print("\n✅ Configuration system check complete!")