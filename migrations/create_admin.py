#!/usr/bin/env python3
"""
Script to create an admin user in the database.
This script uses environment variables if available, otherwise falls back to defaults.
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to the path to import app
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Load environment variables from .env file
env_path = Path(os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))) / '.env'
load_dotenv(dotenv_path=env_path)

from app import create_app, db
from app.models import User, UserRoles

def create_admin():
    app = create_app()
    with app.app_context():
        # Get admin credentials from environment or use defaults
        admin_email = os.environ.get('ADMIN_EMAIL', 'admin@example.com')
        admin_password = os.environ.get('ADMIN_PASSWORD', 'adminpass')
        admin_first_name = os.environ.get('ADMIN_FIRST_NAME', 'Admin')
        admin_last_name = os.environ.get('ADMIN_LAST_NAME', 'User')
        admin_username = os.environ.get('ADMIN_USERNAME', 'admin')
        
        print(f"Attempting to create/update admin user: {admin_email}")
        print(f"Using environment values from: {env_path}")
        
        # Check if admin already exists
        admin = User.query.filter_by(email=admin_email).first()
        
        if not admin:
            # Create new admin user
            admin = User(
                username=admin_username or admin_email.split('@')[0],  # Use username or part of email
                email=admin_email,
                first_name=admin_first_name,
                last_name=admin_last_name,
                role=UserRoles.ADMIN.value,
                _is_admin=True
            )
            admin.set_password(admin_password)
            db.session.add(admin)
            db.session.commit()
            print(f'Admin user {admin_email} created successfully')
        else:
            # Update admin role and password if admin exists
            admin.role = UserRoles.ADMIN.value
            admin._is_admin = True
            admin.first_name = admin_first_name
            admin.last_name = admin_last_name
            if admin_username:
                admin.username = admin_username
            admin.set_password(admin_password)
            db.session.commit()
            print(f'Admin user {admin_email} updated successfully')

if __name__ == '__main__':
    create_admin() 