"""
User model fix that handles the PostgreSQL 'users' vs SQLite 'user' table name discrepancy.
This module provides functions to patch the User model at runtime.
"""
from sqlalchemy import event, inspect
from flask import current_app

def get_user_table_name():
    """Return the appropriate table name based on database dialect"""
    from app import db
    
    try:
        dialect = db.engine.dialect.name
        if dialect == 'postgresql':
            return 'users'
        else:
            return 'user'
    except Exception as e:
        # If we can't determine the dialect (e.g., outside app context or db not initialized)
        from flask import current_app
        current_app.logger.warning(f"Could not determine database dialect: {e}")
        return 'user'  # Default to 'user' as a safer option

def patch_user_model():
    """Patch the User model to use the correct table name based on database dialect"""
    from app.models import User
    from app import db
    
    try:
        # Get the correct table name for the current dialect
        table_name = get_user_table_name()
        
        # Update the model's __tablename__ attribute
        if User.__tablename__ != table_name:
            User.__tablename__ = table_name
            
            # Force SQLAlchemy to clear and rebuild the model registry
            db.Model.metadata.clear()
            
            # Log the change
            current_app.logger.info(f"Patched User model to use table '{table_name}'")
        else:
            current_app.logger.info(f"User model already using correct table name '{table_name}'")
            
        return True
    except Exception as e:
        current_app.logger.error(f"Error patching User model: {e}")
        return False
    
def patch_user_loader():
    """Patch the Flask-Login user_loader to handle table name differences"""
    from app import db, login_manager
    from app.models import User
    from sqlalchemy import text
    
    try:
        # Get the database dialect
        dialect = db.engine.dialect.name
        
        # Define a new user loader function that works with both dialects
        @login_manager.user_loader
        def load_user(id):
            """Fixed user loader that uses the correct table name for both database types"""
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
                from flask import current_app
                current_app.logger.error(f"Error in patched load_user: {e}")
                
                # Fallback to ORM
                try:
                    return User.query.get(int(id))
                except Exception as orm_error:
                    current_app.logger.error(f"ORM fallback also failed: {orm_error}")
                    return None
        
        from flask import current_app
        current_app.logger.info(f"Patched user_loader to handle {dialect} database")
        return True
    except Exception as e:
        from flask import current_app
        current_app.logger.error(f"Error patching user_loader: {e}")
        return False