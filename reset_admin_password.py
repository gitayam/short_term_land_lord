#!/usr/bin/env python3
"""
Script to reset admin password.
"""
from app import create_app, db
from app.models import User
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def reset_admin_password():
    """Reset the password for an admin user."""
    # Get admin credentials from environment
    admin_email = os.environ.get('ADMIN_EMAIL')
    admin_password = os.environ.get('ADMIN_PASSWORD')
    
    if not admin_email or not admin_password:
        print('Admin credentials not fully specified in environment variables.')
        print('Please set ADMIN_EMAIL and ADMIN_PASSWORD in your .env file.')
        return
    
    app = create_app()
    with app.app_context():
        # Find the admin user
        admin_user = User.query.filter_by(email=admin_email).first()
        
        if not admin_user:
            print(f"No user found with email: {admin_email}")
            return
        
        # Update the password
        admin_user.set_password(admin_password)
        db.session.commit()
        
        print(f"Password updated successfully for user: {admin_email}")
        print(f"You can now log in with email: {admin_email} and the password from your .env file.")

if __name__ == '__main__':
    reset_admin_password()
