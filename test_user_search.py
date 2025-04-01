#!/usr/bin/env python
"""
Test script for user search functionality.
"""
import sys
from pathlib import Path

# Add the parent directory to sys.path
parent_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(parent_dir))

from app import create_app, db
from sqlalchemy import text, inspect
from app.models import User

def test_user_search():
    """Test the user search functionality"""
    print("Testing user search functionality...")
    
    # Create app context
    app = create_app()
    
    with app.app_context():
        # Test database dialect detection
        dialect = db.engine.dialect.name
        print(f"Detected database dialect: {dialect}")
        
        # Test table name
        print(f"\nUser model table name: {User.__tablename__}")
        
        # Test direct SQL search
        print("\nTesting direct SQL search...")
        search_term = "test"
        try:
            # Use direct SQL query
            sql = text(f"""
                SELECT id, email, first_name, last_name 
                FROM {User.__tablename__}
                WHERE email LIKE :search 
                   OR first_name LIKE :search 
                   OR last_name LIKE :search
            """)
            result = db.session.execute(sql, {'search': f'%{search_term}%'})
            users = result.fetchall()
            
            if users:
                print(f"Found {len(users)} users matching '{search_term}':")
                for user in users:
                    print(f"- {user.first_name} {user.last_name} ({user.email})")
            else:
                print(f"No users found matching '{search_term}'")
        except Exception as e:
            print(f"Error in direct SQL search: {e}")
        
        # Test ORM search
        print("\nTesting ORM search...")
        try:
            users = User.query.filter(
                (User.first_name.ilike(f'%{search_term}%')) |
                (User.last_name.ilike(f'%{search_term}%')) |
                (User.email.ilike(f'%{search_term}%'))
            ).all()
            
            if users:
                print(f"Found {len(users)} users matching '{search_term}':")
                for user in users:
                    print(f"- {user.first_name} {user.last_name} ({user.email})")
            else:
                print(f"No users found matching '{search_term}'")
        except Exception as e:
            print(f"Error in ORM search: {e}")
        
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
        
        print("\nUser search test complete!")

if __name__ == "__main__":
    test_user_search() 