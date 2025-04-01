#!/usr/bin/env python
"""
Test script for user model compatibility.
"""
import sys
from pathlib import Path

# Add the parent directory to sys.path
parent_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(parent_dir))

from app import create_app, db
from sqlalchemy import text, inspect
from app.models import User

def test_user_compatibility():
    """Test the user model compatibility"""
    print("Testing user model compatibility...")
    
    # Create app context
    app = create_app()
    
    with app.app_context():
        # Test database dialect detection
        dialect = db.engine.dialect.name
        print(f"Detected database dialect: {dialect}")
        
        # Test table name
        print(f"\nUser model table name: {User.__tablename__}")
        
        # Test table existence
        print("\nTesting table existence...")
        try:
            inspector = inspect(db.engine)
            if User.__tablename__ in inspector.get_table_names():
                print(f"Table '{User.__tablename__}' exists")
            else:
                print(f"Table '{User.__tablename__}' does not exist")
        except Exception as e:
            print(f"Error checking table existence: {e}")
        
        # Test column existence
        print("\nTesting column existence...")
        try:
            inspector = inspect(db.engine)
            columns = inspector.get_columns(User.__tablename__)
            if columns:
                print(f"Found columns: {', '.join(col['name'] for col in columns)}")
            else:
                print(f"No columns found in table '{User.__tablename__}'")
        except Exception as e:
            print(f"Error checking columns: {e}")
        
        # Test user creation
        print("\nTesting user creation...")
        try:
            test_user = User(
                email="test@example.com",
                first_name="Test",
                last_name="User"
            )
            db.session.add(test_user)
            db.session.commit()
            print("Successfully created test user")
            
            # Clean up
            db.session.delete(test_user)
            db.session.commit()
            print("Successfully cleaned up test user")
        except Exception as e:
            print(f"Error in user creation test: {e}")
            db.session.rollback()
        
        print("\nUser compatibility test complete!")

if __name__ == "__main__":
    test_user_compatibility() 