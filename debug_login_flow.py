#!/usr/bin/env python3
"""
Debug script to test login flow step by step
"""

import requests
import json
from bs4 import BeautifulSoup

def test_login_flow():
    """Test the complete login flow"""
    base_url = "https://short-term-landlord-dot-speech-memorization.uc.r.appspot.com"
    session = requests.Session()
    
    print("🧪 Testing Login Flow")
    print("=" * 50)
    
    # Step 1: Get login form
    print("1. Getting login form...")
    login_page = session.get(f"{base_url}/auth/login")
    print(f"   Status: {login_page.status_code}")
    
    if login_page.status_code != 200:
        print("❌ Failed to load login page")
        return False
    
    # Step 2: Parse form for CSRF token
    soup = BeautifulSoup(login_page.content, 'html.parser')
    csrf_token = None
    csrf_input = soup.find('input', {'name': 'csrf_token'})
    if csrf_input:
        csrf_token = csrf_input.get('value')
        print(f"   CSRF Token: {'Found' if csrf_token else 'Not found'}")
    else:
        print("   CSRF Token: Not required")
    
    # Step 3: Attempt login
    print("\n2. Attempting login...")
    login_data = {
        'email': 'admin@landlord.com',
        'password': 'admin123',
        'submit': 'Sign In'
    }
    
    if csrf_token:
        login_data['csrf_token'] = csrf_token
    
    login_response = session.post(f"{base_url}/auth/login", data=login_data, allow_redirects=False)
    print(f"   Status: {login_response.status_code}")
    print(f"   Headers: {dict(login_response.headers)}")
    
    # Step 4: Check for redirect
    if login_response.status_code in [302, 301]:
        redirect_url = login_response.headers.get('Location', 'No redirect location')
        print(f"   Redirect to: {redirect_url}")
        
        # Follow redirect
        if redirect_url.startswith('/'):
            redirect_url = base_url + redirect_url
        
        dashboard_response = session.get(redirect_url)
        print(f"   Dashboard Status: {dashboard_response.status_code}")
        
        if dashboard_response.status_code == 200:
            if 'dashboard' in dashboard_response.text.lower() or 'welcome' in dashboard_response.text.lower():
                print("✅ Login successful - reached dashboard")
                return True
            else:
                print("⚠️  Redirected but not to expected dashboard")
        else:
            print("❌ Dashboard access failed")
    else:
        # No redirect - check response content
        if 'Invalid' in login_response.text or 'error' in login_response.text.lower():
            print("❌ Login failed - invalid credentials")
        elif 'dashboard' in login_response.text.lower():
            print("✅ Login successful - no redirect needed")
            return True
        else:
            print("⚠️  Unclear login state")
            print(f"   Response preview: {login_response.text[:200]}...")
    
    # Step 5: Test session persistence
    print("\n3. Testing session persistence...")
    dashboard_direct = session.get(f"{base_url}/dashboard")
    print(f"   Dashboard direct access: {dashboard_direct.status_code}")
    
    if dashboard_direct.status_code == 200:
        print("✅ Session persisted - can access dashboard")
        return True
    elif dashboard_direct.status_code == 302:
        print("⚠️  Session not persisted - redirected to login")
    else:
        print("❌ Dashboard access denied")
    
    return False

if __name__ == "__main__":
    success = test_login_flow()
    print("\n" + "=" * 50)
    print(f"Overall Result: {'✅ SUCCESS' if success else '❌ FAILED'}")