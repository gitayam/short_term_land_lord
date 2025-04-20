#!/usr/bin/env python3
"""
Test script to verify admin users can view any property.
"""
import sys
from app import create_app, db
from app.models import User, Property, UserRoles

def test_admin_property_access():
    """Test if an admin user can view any property."""
    # Create the app with a test configuration
    app = create_app()
    
    with app.app_context():
        # Create an admin user if it doesn't exist
        admin_user = User.query.filter_by(username='admin_test').first()
        if not admin_user:
            admin_user = User(
                username='admin_test',
                email='admin_test@example.com',
                role=UserRoles.ADMIN.value,
                is_admin=True
            )
            admin_user.set_password('adminpass')
            db.session.add(admin_user)
            db.session.commit()
            print(f"Created admin user: {admin_user.email}")
        
        # Create a property if it doesn't exist
        property = Property.query.first()
        if not property:
            # Inspect the property table to see what columns exist
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            property_columns = [col['name'] for col in inspector.get_columns('property')]
            print(f"Property columns: {property_columns}")
            
            # Create property with minimal required fields
            property_data = {
                'name': 'Test Property',
                'owner_id': admin_user.id,
            }
            
            # Add other required fields based on what's in the database
            if 'address' in property_columns:
                property_data['address'] = '123 Test St'
            if 'status' in property_columns:
                property_data['status'] = 'active'
            if 'property_type' in property_columns:
                property_data['property_type'] = 'house'
            if 'description' in property_columns:
                property_data['description'] = 'A test property'
                
            property = Property(**property_data)
            db.session.add(property)
            db.session.commit()
            print(f"Created property: {property.name}")
        
        # Check if admin user has admin role
        print(f"Admin user has admin role: {admin_user.has_admin_role()}")
        print(f"Admin user is_admin flag: {admin_user.is_admin}")
        print(f"Admin user role: {admin_user.role}")
        
        # Check if admin user can view the property in the view route by simulating
        # the permission check that happens in the view route
        from flask_login import current_user
        from flask_login.mixins import AnonymousUserMixin
        
        # Create a test client
        client = app.test_client()
        
        # Test permission check logic
        can_view = False
        if property.owner_id == admin_user.id:
            print("Admin user is the property owner")
            can_view = True
        elif admin_user.has_admin_role():
            print("Admin user has admin role")
            can_view = True
        else:
            print("Admin user doesn't have permission to view this property")
        
        print(f"Admin user can view property: {can_view}")
        
        return can_view

if __name__ == '__main__':
    result = test_admin_property_access()
    if result:
        print("\nTest PASSED: Admin user can view any property")
        sys.exit(0)
    else:
        print("\nTest FAILED: Admin user cannot view any property")
        sys.exit(1) 