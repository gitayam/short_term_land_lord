#!/usr/bin/env python
"""
Fix for the User model to use the correct table name in PostgreSQL.
This script modifies the User model to use the 'users' table name in PostgreSQL
and the 'user' table name in SQLite.
"""
import sys
from pathlib import Path

# Add the parent directory to sys.path
parent_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(parent_dir))

from app import create_app, db
from sqlalchemy import text, inspect
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

def fix_user_model():
    """Modify the User model __tablename__ attribute at runtime"""
    print("Fixing User model table name...")
    
    # Get the database dialect
    dialect = db.engine.dialect.name
    print(f"Detected database dialect: {dialect}")
    
    # Import the User model 
    from app.models import User
    
    # Check the current table name
    current_table = User.__tablename__
    print(f"Current User model table name: {current_table}")
    
    if dialect == 'postgresql':
        # Change the table name to 'users' for PostgreSQL
        if current_table != 'users':
            print(f"Setting User model __tablename__ to 'users'")
            User.__tablename__ = 'users'
            
            # Clear SQLAlchemy's model registry cache
            # This forces SQLAlchemy to rebuild the model mapping
            db.Model.metadata.clear()
            
            # Test the change
            try:
                # Try to execute a query to test if the User model now works
                user_count = db.session.execute(text("SELECT COUNT(*) FROM users")).scalar()
                print(f"Successfully queried users table - found {user_count} users")
                print("User model table name fixed!")
                return True
            except Exception as e:
                print(f"Error testing User model fix: {e}")
                return False
    else:
        # For SQLite, make sure it's using 'user' table name
        if current_table != 'user':
            print(f"Setting User model __tablename__ to 'user'")
            User.__tablename__ = 'user'
            db.Model.metadata.clear()
            
    print("Model fix complete!")
    return True

def apply_login_manager_fix():
    """Fix the User.query.get usage in the login manager user loader"""
    print("Applying login manager fix...")
    
    # Detect dialect
    dialect = db.engine.dialect.name
    
    # Import the necessary modules
    from app import login_manager
    from app.models import User
    
    # Get the existing user loader
    original_loader = login_manager.user_loader
    
    if dialect == 'postgresql':
        # Replace the user loader with a fixed version
        @login_manager.user_loader
        def load_user(id):
            """Fixed user loader that uses direct SQL for PostgreSQL"""
            try:
                # Use direct SQL query instead of ORM
                sql = text("SELECT * FROM users WHERE id = :user_id")
                result = db.session.execute(sql, {'user_id': int(id)})
                row = result.fetchone()
                
                if row:
                    # Create a User instance manually
                    user = User()
                    for key in row._mapping.keys():
                        setattr(user, key, row._mapping[key])
                    return user
                return None
            except Exception as e:
                print(f"Error in load_user: {e}")
                return None
                
        print("Login manager fixed to use 'users' table in PostgreSQL")
    
    print("Login manager fix complete!")
    return True

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        # Apply model fix
        fix_user_model()
        
        # Fix login manager
        apply_login_manager_fix() 