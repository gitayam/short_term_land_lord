#!/usr/bin/env python
"""
Fix for SQLite users table - adds missing columns.
This script directly adds the username, authentik_id, signal_identity, attributes columns to the SQLite database.
"""
import sys
from pathlib import Path
import sqlite3

# Add the parent directory to sys.path
parent_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(parent_dir))

from app import create_app, db

def add_sqlite_columns():
    """Add missing columns to user table in SQLite"""
    print("Adding missing columns to user table in SQLite...")

    # Get the SQLite database path from the app config
    app = create_app()
    db_path = app.config.get('SQLALCHEMY_DATABASE_URI', '').replace('sqlite:///', '')

    if not db_path or not Path(db_path).exists():
        db_path = 'app.db'  # Default SQLite database name

    print(f"Using SQLite database at: {db_path}")

    # Connect to the SQLite database
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Get the columns that exist in the user table
        cursor.execute("PRAGMA table_info(user)")
        existing_columns = [row[1] for row in cursor.fetchall()]
        print(f"Existing columns: {existing_columns}")

        # List of columns to add with their types
        columns_to_add = {
            'username': 'TEXT',
            'authentik_id': 'TEXT',
            'signal_identity': 'TEXT',
            'attributes': 'TEXT',
            'is_admin': 'BOOLEAN DEFAULT 0',
            'is_active': 'BOOLEAN DEFAULT 1',
            'date_joined': 'TIMESTAMP',
            'last_login': 'TIMESTAMP'
        }

        # Add each missing column
        for column, column_type in columns_to_add.items():
            if column not in existing_columns:
                try:
                    cursor.execute(f"ALTER TABLE user ADD COLUMN {column} {column_type}")
                    print(f"Added column '{column}' with type '{column_type}'")
                except sqlite3.Error as e:
                    print(f"Error adding column '{column}': {e}")

        # Create an index on username if it doesn't exist
        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS ix_user_username ON user (username)")
            print("Created index on username column")
        except sqlite3.Error as e:
            print(f"Error creating index on username: {e}")

        # Update date_joined to be the same as created_at for existing rows
        try:
            cursor.execute("UPDATE user SET date_joined = created_at WHERE date_joined IS NULL")
            print("Updated date_joined values from created_at")
        except sqlite3.Error as e:
            print(f"Error updating date_joined: {e}")

        # Commit all changes
        conn.commit()
        print("Committed all changes")

    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
    finally:
        if conn:
            conn.close()

    print("SQLite fix complete!")

if __name__ == "__main__":
    add_sqlite_columns()