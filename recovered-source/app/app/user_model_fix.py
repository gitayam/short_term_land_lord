#!/usr/bin/env python

"""
This script fixes the User model to ensure it uses the correct table name.

Since we're now using a static table name of 'users' for all environments, this script
is simplified to just ensure consistency.
"""

# Import Flask directly to avoid circular imports
from flask import current_app
from sqlalchemy import text
import logging

def get_user_table_name():
    """Return the user table name - always 'users' now"""
    return 'users'

def get_user_fk_target():
    """Return the foreign key target for User model - always 'users.id' now"""
    return 'users.id'

def patch_user_model():
    """
    Ensure User table name is consistent across all database operations.
    This function is called from app/__init__.py during app initialization.
    """
    try:
        from app import db
        from app.models import User
        
        # Set the tablename to 'users'
        User.__tablename__ = 'users'
        
        # Verify the table exists in the database
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        if 'users' in inspector.get_table_names():
            current_app.logger.info("Users table exists in the database")
        else:
            current_app.logger.warning("Users table does not exist in the database - it will be created if migrations are run")
        
        # Log that we've patched the model
        current_app.logger.info(f"User model patched: tablename={User.__tablename__}")
        
        return True
    except Exception as e:
        current_app.logger.error(f"Failed to patch User model: {e}", exc_info=True)
        return False

def patch_user_loader():
    """
    Ensure user loader uses the consistent table name.
    This function is called from app/__init__.py during app initialization.
    """
    try:
        from app import db, login_manager
        
        @login_manager.user_loader
        def load_user(id):
            """Load user by ID."""
            try:
                # Direct SQL query with consistent table name
                table_name = 'users'  # Always use 'users'
                sql = text(f"SELECT * FROM {table_name} WHERE id = :id")
                result = db.session.execute(sql, {'id': id})
                user_data = result.fetchone()
                
                if user_data:
                    from app.models import User
                    user = User()
                    for key, value in user_data._mapping.items():
                        setattr(user, key, value)
                    return user
                
                # Fallback to ORM query
                from app.models import User
                return User.query.get(int(id))
            except Exception as e:
                current_app.logger.error(f"Error loading user: {e}", exc_info=True)
                return None
        
        current_app.logger.info("User loader patched to use consistent table name")
        return True
    except Exception as e:
        current_app.logger.error(f"Failed to patch user loader: {e}", exc_info=True)
        return False

def fix_user_model():
    """
    Run the patching process for the User model and user loader.
    This can be called as a standalone function to fix models.
    """
    from flask import Flask
    app = Flask(__name__)
    
    # Import after Flask app creation to avoid circular imports
    from app import db
    
    with app.app_context():
        success_model = patch_user_model()
        success_loader = patch_user_loader()
        
        return success_model and success_loader

if __name__ == "__main__":
    # Allow running this as a script to fix models
    fix_user_model()