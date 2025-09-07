#!/usr/bin/env python3
"""
Script to verify and fix admin role issues
"""
import sys
import os

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models import User, UserRoles
from flask import current_app

app = create_app()
with app.app_context():
    # Get all users with admin privileges (either by role or is_admin flag)
    admin_users = User.query.filter((User.role == UserRoles.ADMIN.value) | (User.is_admin == True)).all()
    
    print(f"Found {len(admin_users)} admin users:")
    for user in admin_users:
        print(f"- {user.email}")
        print(f"  Username: {user.username}")
        print(f"  Role: {user.role}")
        print(f"  is_admin flag: {user.__dict__.get('is_admin', False)}")
        print(f"  has_admin_role: {user.has_admin_role}")
        print(f"  is_admin property: {user.is_admin}")
        
        # Ensure both the role and is_admin flag are set correctly
        if user.role != UserRoles.ADMIN.value or not user.__dict__.get('is_admin', False):
            print(f"  Fixing admin role for {user.email}...")
            user.role = UserRoles.ADMIN.value
            user.__dict__['is_admin'] = True
            db.session.add(user)
    
    # Commit changes if any were made
    if db.session.dirty:
        db.session.commit()
        print("Fixed admin role issues and saved changes.")
    else:
        print("No admin role issues found.")
    
    # Print instructions for manually setting an admin
    print("\nTo manually make a user an admin, run the following in a Flask shell:")
    print("from app.models import User, UserRoles")
    print("user = User.query.filter_by(email='user@example.com').first()")
    print("user.role = UserRoles.ADMIN.value")
    print("user.is_admin = True")
    print("db.session.commit()") 