#!/usr/bin/env python3
"""
Add phone column to the users table.
This script adds the phone column to the users table if it doesn't exist.
"""

import os
import sys

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import text, inspect
from app import create_app, db

def add_user_phone_field():
    """Add phone column to the users table if it doesn't exist"""
    app = create_app()

    with app.app_context():
        inspector = inspect(db.engine)

        print("Checking users table columns...")

        if 'users' not in inspector.get_table_names():
            print("Users table does not exist, skipping migration")
            return False

        columns = {col['name']: col for col in inspector.get_columns('users')}
        changes_made = False

        # Add phone column
        if 'phone' not in columns:
            print("Adding phone column to users table...")
            with db.engine.connect() as conn:
                with conn.begin():  # Start a transaction
                    conn.execute(text("ALTER TABLE users ADD COLUMN phone VARCHAR(20)"))
                print("Added phone column")
            changes_made = True

        if changes_made:
            print("User phone column added successfully!")
        else:
            print("User phone column already exists")

        return changes_made

if __name__ == '__main__':
    try:
        result = add_user_phone_field()
        if result:
            print("Added user phone field successfully!")
        else:
            print("No changes needed for user phone field.")
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)