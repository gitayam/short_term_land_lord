#!/usr/bin/env python3
"""
Script to create an admin user in the database.
"""
import os
import sys

# Add parent directory to the path to import app
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app, db
from app.models import User, UserRoles

def create_admin():
    app = create_app()
    with app.app_context():
        # Check if admin already exists
        admin = User.query.filter_by(email='admin@example.com').first()
        
        if not admin:
            # Create new admin user
            admin = User(
                username='admin',
                email='admin@example.com',
                first_name='Admin',
                last_name='User',
                role=UserRoles.ADMIN.value,
                _is_admin=True
            )
            admin.set_password('adminpass')
            db.session.add(admin)
            db.session.commit()
            print('Admin user created successfully')
        else:
            # Update admin role and password if admin exists
            admin.role = UserRoles.ADMIN.value
            admin._is_admin = True
            admin.set_password('adminpass')
            db.session.commit()
            print('Admin user updated successfully')

if __name__ == '__main__':
    create_admin() 