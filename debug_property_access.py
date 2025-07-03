#!/usr/bin/env python3

from app import create_app, db
from app.models import User, UserRoles, Property
from config import TestConfig

def debug_property_access():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        
        # Create test users
        owner = User(
            first_name='Test',
            last_name='Owner',
            email='owner@example.com',
            role=UserRoles.PROPERTY_OWNER.value
        )
        owner.set_password('test_password')
        
        tenant = User(
            first_name='Test',
            last_name='Tenant',
            email='tenant@example.com',
            role=UserRoles.TENANT.value
        )
        tenant.set_password('test_password')
        
        db.session.add_all([owner, tenant])
        db.session.commit()
        
        # Create test property owned by tenant
        property = Property(
            name='Test Property',
            description='A test property',
            address='123 Test St, Test City, Test State 12345',
            street_address='123 Test St',
            city='Test City',
            state='Test State',
            zip_code='12345',
            country='Test Country',
            owner_id=tenant.id  # Make tenant the owner
        )
        
        db.session.add(property)
        db.session.commit()
        
        print(f"Property owner_id: {property.owner_id}")
        print(f"Tenant id: {tenant.id}")
        print(f"Property owner: {property.owner}")
        print(f"Tenant is_property_owner: {tenant.is_property_owner}")
        print(f"Property is_visible_to(tenant): {property.is_visible_to(tenant)}")
        print(f"Property is_visible_to(owner): {property.is_visible_to(owner)}")
        
        # Test the specific condition from the route
        if tenant.is_property_owner and property.owner_id == tenant.id:
            print("✅ Tenant should have access to property")
        else:
            print("❌ Tenant should NOT have access to property")
            print(f"  tenant.is_property_owner: {tenant.is_property_owner}")
            print(f"  property.owner_id == tenant.id: {property.owner_id == tenant.id}")

if __name__ == '__main__':
    debug_property_access() 