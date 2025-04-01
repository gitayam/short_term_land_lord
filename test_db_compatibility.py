#!/usr/bin/env python
"""
Test script for database compatibility utilities.
"""
import sys
from pathlib import Path

# Add the parent directory to sys.path
parent_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(parent_dir))

from app import create_app, db
from sqlalchemy import text
from app.models import User

def run_tests():
    """Run database compatibility tests"""
    print("Starting database compatibility tests...")
    
    # Create app context
    app = create_app()
    
    with app.app_context():
        # Test database dialect detection
        dialect = db.engine.dialect.name
        print(f"Detected database dialect: {dialect}")
        
        # Test table name
        print(f"\nUser model table name: {User.__tablename__}")
        
        print("\nTesting get_user_by_id...")
        try:
            # Try to get user with ID 1
            sql = text(f"SELECT * FROM {User.__tablename__} WHERE id = :id")
            result = db.session.execute(sql, {'id': 1})
            user_data = result.fetchone()
            
            if user_data:
                user = User()
                for key, value in user_data._mapping.items():
                    setattr(user, key, value)
                print(f"Found user with ID 1: {user.email}")
            else:
                print("No user found with ID 1")
        except Exception as e:
            print(f"Error getting user by ID: {e}")
        
        print("\nTesting user search...")
        try:
            # Test user search with a simple query
            search_term = "test"
            sql = text(f"""
                SELECT * FROM {User.__tablename__}
                WHERE email LIKE :search
                   OR first_name LIKE :search
                   OR last_name LIKE :search
            """)
            result = db.session.execute(sql, {'search': f'%{search_term}%'})
            users = result.fetchall()
            
            if users:
                print(f"Found {len(users)} users matching '{search_term}':")
                for user_data in users:
                    user = User()
                    for key, value in user_data._mapping.items():
                        setattr(user, key, value)
                    print(f"- {user.get_full_name()} ({user.email})")
            else:
                print(f"No users found matching '{search_term}'")
        except Exception as e:
            print(f"Error in user search: {e}")
        
        print("\nDatabase compatibility tests complete!")

if __name__ == "__main__":
    run_tests() 