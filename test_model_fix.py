#!/usr/bin/env python
"""
Test script for User model fixes.
This verifies that the User model works correctly with both PostgreSQL and SQLite.
"""
import sys
from pathlib import Path

# Add the parent directory to sys.path
parent_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(parent_dir))

from app import create_app, db
from sqlalchemy import text

def test_user_model():
    """Test that User model works correctly with the current database"""
    print("Testing User model with current database...")
    
    # Get the database dialect
    dialect = db.engine.dialect.name
    print(f"Database dialect: {dialect}")
    
    # Import the User model
    from app.models import User
    print(f"User model table name: {User.__tablename__}")
    
    # Check for correct table name
    if dialect == 'postgresql' and User.__tablename__ != 'users':
        print("ERROR: User model should use 'users' table for PostgreSQL")
    elif dialect == 'sqlite' and User.__tablename__ != 'user':
        print("ERROR: User model should use 'user' table for SQLite")
    else:
        print("✅ Table name is correct for this database")
    
    # Test direct table access
    try:
        # Get direct table name
        table_name = User.__tablename__
        
        # Execute a direct query
        result = db.session.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
        count = result.scalar()
        print(f"✅ Direct table query successful: found {count} users")
        
        # List all users
        if count > 0:
            result = db.session.execute(text(f"SELECT id, email, first_name, last_name FROM {table_name} LIMIT 5"))
            users = result.fetchall()
            print("Users found:")
            for user in users:
                print(f"  - User #{user[0]}: {user[2]} {user[3]} ({user[1]})")
                
    except Exception as e:
        print(f"❌ Error accessing table directly: {e}")
    
    # Test ORM access
    try:
        # Query all users using the ORM
        users = User.query.all()
        print(f"✅ ORM query successful: found {len(users)} users")
        
        # Show the first few users
        if users:
            for user in users[:5]:
                print(f"  - User #{user.id}: {user.first_name} {user.last_name} ({user.email})")
    except Exception as e:
        print(f"❌ Error using ORM: {e}")
    
    # Test user loading
    try:
        # Import flask_login user loading function
        from flask_login import _get_user
        from flask import current_app
        
        # Try to load user with ID 1
        user_id = 1
        print(f"Testing user_loader with ID {user_id}...")
        
        # Get the user_loader function
        user_loader = current_app.login_manager._user_callback
        
        # Call it directly
        user = user_loader(user_id)
        
        if user:
            print(f"✅ user_loader successful: loaded User #{user.id}: {user.get_full_name()} ({user.email})")
        else:
            print(f"⚠️ No user found with ID {user_id}")
    except Exception as e:
        print(f"❌ Error testing user_loader: {e}")
    
    print("User model test complete!")

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        test_user_model() 