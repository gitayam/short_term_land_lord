import os
import sys

# Add parent directory to path so we can import app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models import User, Property, UserRoles

def test_admin_access():
    # Create app context
    app = create_app()
    with app.app_context():
        # Get admin user
        admin = User.query.filter_by(username='admin').first()
        print(f'Admin exists: {admin is not None}')
        
        if not admin:
            print('Admin not found, creating one...')
            admin = User(
                username='admin',
                email='admin@example.com',
                first_name='System',
                last_name='Admin',
                role=UserRoles.ADMIN.value
            )
            admin.__dict__['is_admin'] = True
            admin.set_password('adminpass')
            db.session.add(admin)
            db.session.commit()
            print(f'Admin created with ID: {admin.id}')
        
        print(f'Admin has admin role: {admin.has_admin_role()}')
        
        # Get all properties
        properties = Property.query.all()
        print(f'Number of properties: {len(properties)}')
        
        # Check if properties are visible to admin
        for prop in properties:
            print(f'Property {prop.id}: {prop.name} - Visible to admin: {prop.is_visible_to(admin)}')
            
        # Create a test property if none exists
        if not properties:
            print('No properties found, creating a test property...')
            owner = User.query.filter(User.username != 'admin').first()
            if not owner:
                print('No non-admin users found to own the property')
                return
            
            test_property = Property(
                name='Test Property',
                address='123 Test St, Testville',
                owner_id=owner.id,
                property_type='house'
            )
            db.session.add(test_property)
            db.session.commit()
            print(f'Test property created with ID: {test_property.id}')
            print(f'Visible to admin: {test_property.is_visible_to(admin)}')

if __name__ == '__main__':
    test_admin_access() 