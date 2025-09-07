#!/usr/bin/env python3
"""
Script to manually create an admin user from environment variables.
This script is meant to be run inside the Docker container.
"""
from flask import current_app
from app import create_app, db
from app.models import User, UserRoles

def create_admin_user():
    """Create an admin user from environment variables"""
    # Create app context
    app = create_app()
    with app.app_context():
        # Get admin credentials from environment
        admin_email = current_app.config.get('ADMIN_EMAIL')
        admin_username = current_app.config.get('ADMIN_USERNAME')
        admin_password = current_app.config.get('ADMIN_PASSWORD')
        admin_first_name = current_app.config.get('ADMIN_FIRST_NAME', 'System')
        admin_last_name = current_app.config.get('ADMIN_LAST_NAME', 'Administrator')
        
        print(f"Admin email from config: {admin_email}")
        print(f"Admin password from config: {'*****' if admin_password else 'Not set'}")
        
        if not admin_email or not admin_password:
            print('Admin credentials not fully specified in environment variables.')
            print('Please set ADMIN_EMAIL and ADMIN_PASSWORD in your .env file.')
            return
        
        # Check if admin user already exists
        query = User.query.filter(User.email == admin_email)
        if admin_username:
            from sqlalchemy import or_
            query = query.union(User.query.filter(User.username == admin_username))
        
        existing_admin = query.first()
        
        if existing_admin:
            print(f"Admin user already exists: {existing_admin.email}")
            # Update admin role if needed
            if existing_admin.role != UserRoles.ADMIN.value:
                existing_admin.role = UserRoles.ADMIN.value
                existing_admin.is_admin = True
                db.session.commit()
                print(f"Updated user {existing_admin.email} to admin role")
            return
        
        # Create new admin user
        admin_user = User(
            email=admin_email,
            first_name=admin_first_name,
            last_name=admin_last_name,
            role=UserRoles.ADMIN.value,
            is_admin=True
        )
        
        # Set username if provided
        if admin_username:
            admin_user.username = admin_username
        
        admin_user.set_password(admin_password)
        
        db.session.add(admin_user)
        db.session.commit()
        print(f"Created admin user: {admin_email}")

if __name__ == '__main__':
    create_admin_user()
