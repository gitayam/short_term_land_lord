#!/usr/bin/env python
"""
Test script for User model fixes.
"""
import sys
from pathlib import Path

# Add the parent directory to sys.path
parent_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(parent_dir))

from app import create_app, db
from sqlalchemy import text, inspect
from app.models import User

def test_user_model():
    """Test the User model functionality"""
    print("Starting User model test...")
    
    # Create app context
    app = create_app()
    
    with app.app_context():
        # Test database dialect detection
        dialect = db.engine.dialect.name
        print(f"Detected database dialect: {dialect}")
        
        # Test table name
        print(f"\nUser model table name: {User.__tablename__}")
        
        # Test direct table access
        print("\nTesting direct table access...")
        try:
            # Count users
            result = db.session.execute(text(f"SELECT COUNT(*) FROM {User.__tablename__}"))
            count = result.scalar()
            print(f"Found {count} users in table")
            
            # List users
            result = db.session.execute(text(f"SELECT id, email FROM {User.__tablename__} LIMIT 5"))
            users = result.fetchall()
            if users:
                print("\nFirst 5 users:")
                for user in users:
                    print(f"- ID: {user.id}, Email: {user.email}")
            else:
                print("No users found in table")
        except Exception as e:
            print(f"Error accessing table directly: {e}")
        
        # Test ORM access
        print("\nTesting ORM access...")
        try:
            users = User.query.all()
            print(f"Found {len(users)} users via ORM")
            if users:
                print("\nFirst 5 users via ORM:")
                for user in users[:5]:
                    print(f"- ID: {user.id}, Email: {user.email}")
        except Exception as e:
            print(f"Error accessing via ORM: {e}")
        
        # Test user loading
        print("\nTesting user loading...")
        try:
            if users:
                test_id = users[0].id
                user = User.query.get(test_id)
                if user:
                    print(f"Successfully loaded user {test_id}: {user.email}")
                else:
                    print(f"Could not load user {test_id}")
        except Exception as e:
            print(f"Error loading user: {e}")
        
        print("\nUser model test complete!")

if __name__ == "__main__":
    test_user_model() 