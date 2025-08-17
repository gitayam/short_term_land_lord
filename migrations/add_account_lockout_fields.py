#!/usr/bin/env python3
"""
Migration script to add account lockout fields to User model
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import User
from sqlalchemy import text

def add_account_lockout_fields():
    """Add account lockout fields to users table"""
    app = create_app()
    with app.app_context():
        try:
            print("Adding account lockout fields to users table...")
            
            # Check if columns already exist
            inspector = db.inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('users')]
            
            # Add failed_login_attempts column
            if 'failed_login_attempts' not in columns:
                with db.engine.begin() as conn:
                    conn.execute(text("""
                        ALTER TABLE users 
                        ADD COLUMN failed_login_attempts INTEGER DEFAULT 0
                    """))
                print("✓ Added failed_login_attempts column")
            else:
                print("• failed_login_attempts column already exists")
            
            # Add locked_until column
            if 'locked_until' not in columns:
                with db.engine.begin() as conn:
                    conn.execute(text("""
                        ALTER TABLE users 
                        ADD COLUMN locked_until DATETIME NULL
                    """))
                print("✓ Added locked_until column")
            else:
                print("• locked_until column already exists")
            
            # Add last_failed_login column
            if 'last_failed_login' not in columns:
                with db.engine.begin() as conn:
                    conn.execute(text("""
                        ALTER TABLE users 
                        ADD COLUMN last_failed_login DATETIME NULL
                    """))
                print("✓ Added last_failed_login column")
            else:
                print("• last_failed_login column already exists")
            
            # Initialize existing users with default values
            users_updated = db.session.query(User).filter(
                User.failed_login_attempts.is_(None)
            ).update({
                'failed_login_attempts': 0
            })
            
            db.session.commit()
            
            if users_updated > 0:
                print(f"✓ Initialized {users_updated} existing users with default lockout values")
            
            print("✓ Account lockout fields migration completed successfully!")
            
        except Exception as e:
            print(f"❌ Migration failed: {str(e)}")
            db.session.rollback()
            return False
        
        return True

if __name__ == '__main__':
    success = add_account_lockout_fields()
    sys.exit(0 if success else 1)