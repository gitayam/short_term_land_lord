#!/usr/bin/env python3
"""
This script adds the missing is_admin column to the users table.
"""

import os
import sys
from sqlalchemy import text, inspect

# Import the app creation function
from app import create_app, db

def add_is_admin_column():
    """Add is_admin column to users table if it doesn't exist"""
    # Create app with the application factory
    app = create_app()

    with app.app_context():
        inspector = inspect(db.engine)

        print("Checking database tables...")
        tables = inspector.get_table_names()
        print(f"Found tables: {tables}")

        if 'users' not in tables:
            print("users table not found! Cannot add column.")
            return False

        # Table exists, check if column exists
        columns = [col['name'] for col in inspector.get_columns('users')]
        print(f"Columns in users table: {columns}")

        # Check for is_admin column
        if 'is_admin' not in columns:
            print("Adding is_admin column to users table...")
            # Add the is_admin column
            with db.engine.connect() as connection:
                connection.execute(text("ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT FALSE"))
                connection.commit()
            print("is_admin column added successfully!")

            # Update admin users
            from app.models import User, UserRoles
            admin_users = User.query.filter_by(role=UserRoles.ADMIN.value).all()
            for user in admin_users:
                print(f"Setting is_admin=True for admin user: {user.email}")
                with db.engine.connect() as connection:
                    connection.execute(
                        text("UPDATE users SET is_admin = TRUE WHERE id = :user_id"),
                        {"user_id": user.id}
                    )
                    connection.commit()

            return True
        else:
            print("is_admin column already exists in users table!")
            return False

if __name__ == '__main__':
    try:
        result = add_is_admin_column()
        if result:
            print("Added is_admin column successfully!")
        else:
            print("No changes needed - column already exists or table not found.")
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)