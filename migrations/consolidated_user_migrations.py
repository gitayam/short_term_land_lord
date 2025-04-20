#!/usr/bin/env python3
"""
Consolidated user table migrations script.
This script combines various user-related table migrations into a single script:
1. Creates the users table if it doesn't exist
2. Adds missing columns to user table (phone, username, is_admin, etc.)
3. Fixes the User model to use the correct table name
4. Ensures admin user is created/updated

Usage:
    python consolidated_user_migrations.py
"""
import os
import sys
import secrets
from pathlib import Path
from dotenv import load_dotenv

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load environment variables from .env file
env_path = Path(os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))) / '.env'
load_dotenv(dotenv_path=env_path)

from sqlalchemy import text, inspect
from app import create_app, db
from app.models import User, UserRoles

def ensure_users_table():
    """Ensure the users table exists and has the correct structure"""
    app = create_app()
    
    with app.app_context():
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        
        if 'users' not in inspector.get_table_names():
            print("Creating users table...")
            with db.engine.connect() as conn:
                with conn.begin():
                    # Create users table with all required fields
                    conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY,
                        username VARCHAR(64) UNIQUE,
                        first_name VARCHAR(64),
                        last_name VARCHAR(64),
                        email VARCHAR(120) UNIQUE,
                        phone VARCHAR(20),
                        password_hash VARCHAR(256),
                        role VARCHAR(20),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        is_active BOOLEAN DEFAULT TRUE,
                        is_admin BOOLEAN DEFAULT FALSE,
                        last_login TIMESTAMP,
                        authentik_id VARCHAR(36) UNIQUE,
                        signal_identity VARCHAR(36) UNIQUE,
                        attributes TEXT
                    )
                    """))
                    
                    # Create indexes
                    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_users_email ON users (email)"))
                    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_users_username ON users (username)"))
            
            print("Users table created successfully!")
            return True
        else:
            print("Users table already exists, checking for missing columns...")
            
            # Get existing columns
            columns = {col['name']: col for col in inspector.get_columns('users')}
            changes_made = False
            
            # List of columns to ensure exist, with their SQL types
            required_columns = {
                'username': 'VARCHAR(64)',
                'phone': 'VARCHAR(20)',
                'is_admin': 'BOOLEAN DEFAULT FALSE',
                'is_active': 'BOOLEAN DEFAULT TRUE',
                'password_hash': 'VARCHAR(256)',
                'last_login': 'TIMESTAMP',
                'authentik_id': 'VARCHAR(36)',
                'signal_identity': 'VARCHAR(36)',
                'attributes': 'TEXT'
            }
            
            # Add each missing column
            for column_name, column_type in required_columns.items():
                if column_name not in columns:
                    print(f"Adding {column_name} column to users table...")
                    with db.engine.connect() as conn:
                        with conn.begin():
                            conn.execute(text(f"ALTER TABLE users ADD COLUMN {column_name} {column_type}"))
                    print(f"Added {column_name} column")
                    changes_made = True
            
            if changes_made:
                print("User table updated with missing columns")
                return True
            else:
                print("All required columns already exist in users table")
                return False

def fix_user_model():
    """Ensure the User model uses the correct table name"""
    print("Fixing User model table name...")
    
    # Import the User model 
    from app.models import User
    
    # Check the current table name
    current_table = User.__tablename__
    print(f"Current User model table name: {current_table}")
    
    app = create_app()
    with app.app_context():
        dialect = db.engine.dialect.name
        
        if dialect == 'postgresql':
            # For PostgreSQL, set table name to 'users'
            if current_table != 'users':
                print(f"Setting User model __tablename__ to 'users'")
                User.__tablename__ = 'users'
                
                # Clear SQLAlchemy's model registry cache
                db.Model.metadata.clear()
        else:
            # For SQLite, set table name to 'user'
            if current_table != 'user':
                print(f"Setting User model __tablename__ to 'user'")
                User.__tablename__ = 'user'
                db.Model.metadata.clear()
        
        print("Model fix completed.")
        return True

def create_admin():
    """Create/update admin user using environment variables"""
    app = create_app()
    
    with app.app_context():
        # Get admin credentials from environment or use defaults
        admin_email = os.environ.get('ADMIN_EMAIL', 'admin@example.com')
        admin_password = os.environ.get('ADMIN_PASSWORD', 'adminpass')
        admin_first_name = os.environ.get('ADMIN_FIRST_NAME', 'Admin')
        admin_last_name = os.environ.get('ADMIN_LAST_NAME', 'User')
        admin_username = os.environ.get('ADMIN_USERNAME', 'admin')
        
        print(f"Attempting to create/update admin user: {admin_email}")
        print(f"Using environment values from: {env_path}")
        
        # Check if admin already exists
        admin = User.query.filter_by(email=admin_email).first()
        
        if not admin:
            # Create new admin user
            admin = User(
                username=admin_username or admin_email.split('@')[0],  # Use username or part of email
                email=admin_email,
                first_name=admin_first_name,
                last_name=admin_last_name,
                role=UserRoles.ADMIN.value,
                _is_admin=True
            )
            admin.set_password(admin_password)
            db.session.add(admin)
            db.session.commit()
            print(f'Admin user {admin_email} created successfully')
        else:
            # Update admin role and password if admin exists
            admin.role = UserRoles.ADMIN.value
            admin._is_admin = True
            admin.first_name = admin_first_name
            admin.last_name = admin_last_name
            if admin_username:
                admin.username = admin_username
            admin.set_password(admin_password)
            db.session.commit()
            print(f'Admin user {admin_email} updated successfully')
        
        return True

def run_consolidated_migrations():
    """Run all user-related migrations in the correct order"""
    try:
        print("Starting consolidated user migrations...")
        
        # 1. Ensure users table exists with all required columns
        ensure_users_table()
        
        # 2. Fix the User model to use the correct table name
        fix_user_model()
        
        # 3. Create/update admin user
        create_admin()
        
        print("All user-related migrations completed successfully!")
        return True
        
    except Exception as e:
        print(f"Error in consolidated user migrations: {str(e)}")
        return False

if __name__ == '__main__':
    success = run_consolidated_migrations()
    sys.exit(0 if success else 1) 