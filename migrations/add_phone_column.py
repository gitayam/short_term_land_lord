#!/usr/bin/env python3
"""
Add the phone column to the users table if it's missing.
"""
import os
import sys
from sqlalchemy import text

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from app import create_app, db

def add_phone_column():
    """Add the phone column to users table if it doesn't exist"""
    app = create_app()

    with app.app_context():
        print("Checking for phone column in users table...")

        # Check if the phone column exists
        inspector = db.inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('users')]

        if 'phone' not in columns:
            print("Phone column missing, adding it now...")

            try:
                # Add the phone column using raw SQL
                db.session.execute(text("ALTER TABLE users ADD COLUMN phone VARCHAR(20)"))
                db.session.commit()
                print("Phone column added successfully!")
                return True
            except Exception as e:
                db.session.rollback()
                print(f"Error adding phone column: {str(e)}")
                return False
        else:
            print("Phone column already exists.")
            return True

if __name__ == "__main__":
    success = add_phone_column()
    sys.exit(0 if success else 1)