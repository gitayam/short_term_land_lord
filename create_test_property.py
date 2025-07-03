#!/usr/bin/env python3

from app import create_app, db
from app.models import User, Property

def create_test_property():
    app = create_app()
    with app.app_context():
        # Get the admin user
        admin_user = User.query.filter_by(email='issac@alfaren.xyz').first()
        if not admin_user:
            print("Admin user not found!")
            return
        
        # Check if test property already exists
        existing_property = Property.query.filter_by(name='Test Property').first()
        if existing_property:
            print("Test property already exists!")
            return
        
        # Create test property
        test_property = Property(
            owner_id=admin_user.id,
            name='Test Property',
            address='123 Test Street, Test City, TS 12345',
            description='A test property for development and testing purposes',
            property_type='house',
            status='active',
            street_address='123 Test Street',
            city='Test City',
            state='TS',
            zip_code='12345',
            country='USA',
            bedrooms=3,
            bathrooms=2.5,
            square_feet=2000,
            year_built=2020,
            wifi_network='TestWiFi',
            wifi_password='testpassword123',
            special_instructions='This is a test property for development purposes.',
            entry_instructions='Use the keypad code 1234 to enter.',
            total_beds=4,
            bed_sizes='2 Queen, 2 Twin',
            number_of_tvs=3,
            number_of_showers=2,
            number_of_tubs=1,
            checkin_time='3:00 PM',
            checkout_time='11:00 AM'
        )
        
        db.session.add(test_property)
        db.session.commit()
        
        print(f"Test property created successfully!")
        print(f"Property ID: {test_property.id}")
        print(f"Property Name: {test_property.name}")
        print(f"Property Address: {test_property.address}")

if __name__ == '__main__':
    create_test_property() 