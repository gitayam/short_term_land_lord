#!/usr/bin/env python3
"""
Demo script for the guest invitation system

This script demonstrates the guest invitation system by:
1. Creating a sample guest invitation
2. Simulating the guest registration process
3. Showing the guest dashboard functionality
"""

import os
import sys

# Add the project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from app import create_app, db
from app.models import User, Property, GuestInvitation, UserRoles
from datetime import datetime, timedelta

def create_demo_data():
    """Create demo data for the guest system"""
    app = create_app()
    
    with app.app_context():
        try:
            # Create admin user if needed
            admin = User.query.filter_by(email='admin@demo.com').first()
            if not admin:
                from werkzeug.security import generate_password_hash
                admin = User(
                    email='admin@demo.com',
                    first_name='Demo',
                    last_name='Admin',
                    password_hash=generate_password_hash('admin123'),
                    role=UserRoles.ADMIN.value,
                    is_active=True
                )
                db.session.add(admin)
                db.session.flush()
            
            # Create demo property if needed
            property = Property.query.filter_by(name='Demo Beach House').first()
            if not property:
                property = Property(
                    name='Demo Beach House',
                    address='123 Ocean Boulevard',
                    description='Beautiful beachfront property with ocean views',
                    city='Santa Monica',
                    state='CA',
                    property_type='house',
                    owner_id=admin.id,
                    status='active',
                    guest_access_enabled=True
                )
                db.session.add(property)
                db.session.flush()
            
            # Create guest invitation
            existing_invitation = GuestInvitation.query.filter(
                GuestInvitation.is_active == True,
                GuestInvitation.expires_at > datetime.utcnow()
            ).first()
            
            if not existing_invitation:
                invitation = GuestInvitation.create_invitation(
                    created_by_id=admin.id,
                    property_id=property.id,
                    email='guest@demo.com',
                    guest_name='Demo Guest',
                    expires_in_days=30,
                    notes='Demo invitation for testing'
                )
                db.session.commit()
                
                print("✅ Demo Data Created Successfully!")
                print(f"   Admin Email: admin@demo.com (password: admin123)")
                print(f"   Property: {property.name}")
                print(f"   Guest Invitation Code: {invitation.code}")
                print(f"   Guest Email: guest@demo.com")
                print("")
                
                return {
                    'admin': admin,
                    'property': property,
                    'invitation': invitation
                }
            else:
                print("✅ Demo Data Already Exists!")
                print(f"   Existing Invitation Code: {existing_invitation.code}")
                return {
                    'admin': admin,
                    'property': property,
                    'invitation': existing_invitation
                }
                
        except Exception as e:
            print(f"❌ Error creating demo data: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

def print_demo_urls():
    """Print the demo URLs for testing"""
    print("🌐 Demo URLs (Server running on http://localhost:5002):")
    print("")
    print("📋 Public Guest Pages:")
    print("   • Browse Properties: http://localhost:5002/guest/browse")
    print("   • Registration Help: http://localhost:5002/guest/register/help")
    print("")
    print("🔐 Admin Pages (Login as admin@demo.com / admin123):")
    print("   • Login: http://localhost:5002/auth/login")
    print("   • Manage Invitations: http://localhost:5002/guest/admin/invitations")
    print("   • Create Invitation: http://localhost:5002/guest/admin/invitations/create")
    print("   • Dashboard: http://localhost:5002/dashboard")
    print("")
    print("👤 Guest Features:")
    print("   • Use the invitation code printed above to register")
    print("   • Register at: http://localhost:5002/guest/register/<INVITATION_CODE>")
    print("   • After registration, login and access guest dashboard")
    print("")

def demonstrate_api():
    """Demonstrate the API endpoints"""
    print("🔌 API Endpoints:")
    print("   • Properties API: http://localhost:5002/guest/api/properties")
    print("   • Check invitation status: http://localhost:5002/guest/api/invitation/<CODE>/status")
    print("")

if __name__ == "__main__":
    print("🚀 Setting up Guest Invitation System Demo...")
    print("")
    
    demo_data = create_demo_data()
    
    if demo_data:
        print_demo_urls()
        demonstrate_api()
        
        print("📖 Demo Workflow:")
        print("1. Visit the browse properties page (no login required)")
        print("2. Login as admin to create guest invitations") 
        print("3. Use invitation code to register as a guest")
        print("4. Login as guest to access personalized dashboard")
        print("5. Explore guest booking and property features")
        print("")
        print("🎯 Key Features Demonstrated:")
        print("   ✓ Public property browsing")
        print("   ✓ Invitation code generation")
        print("   ✓ Guest account registration")
        print("   ✓ Role-based access control")
        print("   ✓ Guest dashboard and booking history")
        print("   ✓ Admin invitation management")
        print("")
        print("🔥 Ready for testing! Server should be running on http://localhost:5002")
    else:
        print("❌ Failed to create demo data")
        sys.exit(1)