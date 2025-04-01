"""
User model fix that handles the PostgreSQL 'users' vs SQLite 'user' table name discrepancy.
This module provides functions to patch the User model at runtime.
"""
from sqlalchemy import event, inspect
from flask import current_app

def get_user_table_name():
    """Return the appropriate table name based on database dialect"""
    from app import db
    
    dialect = db.engine.dialect.name
    if dialect == 'postgresql':
        return 'users'
    else:
        return 'user'

def patch_user_model():
    """Patch the User model to use the correct table name based on database dialect"""
    from app.models import User
    from app import db
    
    # Get the correct table name for the current dialect
    table_name = get_user_table_name()
    
    # Update the model's __tablename__ attribute
    if User.__tablename__ != table_name:
        User.__tablename__ = table_name
        
        # Force SQLAlchemy to clear and rebuild the model registry
        db.Model.metadata.clear()
        
        # Log the change
        current_app.logger.info(f"Patched User model to use table '{table_name}'")
    
def patch_user_loader():
    """Patch the Flask-Login user_loader to handle table name differences"""
    from app import db, login
    from app.models import User
    from sqlalchemy import text
    
    # Get the database dialect
    dialect = db.engine.dialect.name
    
    # Only patch for PostgreSQL
    if dialect == 'postgresql':
        @login.user_loader
        def load_user(id):
            """Fixed user loader that uses the correct table name for PostgreSQL"""
            try:
                # Use direct SQL query with the correct table name
                table_name = get_user_table_name()
                sql = text(f"SELECT * FROM {table_name} WHERE id = :user_id")
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
                current_app.logger.error(f"Error in patched load_user: {e}")
                return None
        
        current_app.logger.info("Patched user_loader to handle PostgreSQL 'users' table") 