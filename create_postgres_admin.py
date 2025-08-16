#!/usr/bin/env python3
"""
Create admin user in PostgreSQL database
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import User
from werkzeug.security import generate_password_hash

# Use PostgreSQL configuration
os.environ['FLASK_ENV'] = 'postgres_dev'
os.environ['DATABASE_URL'] = os.environ.get('DATABASE_URL', 'postgresql://landlord:password@127.0.0.1:5432/landlord_prod')

def create_admin():
    """Create admin user in PostgreSQL"""
    
    # Create app with PostgreSQL config
    app = create_app('postgres_dev')
    
    with app.app_context():
        # Check if admin already exists
        admin = User.query.filter_by(username='admin').first()
        if admin:
            print("Admin user already exists!")
            return
        
        # Create admin user
        admin_user = User(
            username='admin',
            email='admin@landlord.com',
            first_name='System',
            last_name='Administrator',
            phone='555-0100',
            password_hash=generate_password_hash('admin123'),
            role='admin'
        )
        
        db.session.add(admin_user)
        
        # Create a cleaner user for testing
        cleaner_user = User(
            username='cleaner1',
            email='cleaner@landlord.com',
            first_name='Jane',
            last_name='Cleaner',
            phone='555-0101',
            password_hash=generate_password_hash('cleaner123'),
            role='cleaner'
        )
        
        db.session.add(cleaner_user)
        
        # Create an owner user for testing
        owner_user = User(
            username='owner1',
            email='owner@landlord.com',
            first_name='John',
            last_name='Owner',
            phone='555-0102',
            password_hash=generate_password_hash('owner123'),
            role='owner'
        )
        
        db.session.add(owner_user)
        
        # Commit all users
        db.session.commit()
        
        print("✅ Successfully created users:")
        print("  - admin@landlord.com / admin123 (Admin)")
        print("  - cleaner@landlord.com / cleaner123 (Cleaner)")
        print("  - owner@landlord.com / owner123 (Owner)")

if __name__ == "__main__":
    try:
        create_admin()
    except Exception as e:
        print(f"❌ Failed to create admin user: {e}")
        sys.exit(1)