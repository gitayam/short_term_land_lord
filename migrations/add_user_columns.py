#!/usr/bin/env python
"""
Fix for PostgreSQL users table - adds missing columns.
This script directly adds the username, authentik_id, signal_identity, and attributes columns.
"""
import os
import sys
from pathlib import Path
import sqlalchemy as sa

# Add the parent directory to sys.path
parent_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(parent_dir))

from app import create_app, db

def add_user_columns():
    """Add missing columns to users table in PostgreSQL"""
    print("Adding missing columns to users table...")

    # Check if we're using PostgreSQL
    db_uri = db.engine.url
    if 'postgres' not in db_uri.drivername:
        print(f"Not a PostgreSQL database ({db_uri.drivername}). No fixes needed.")
        return

    # Get raw connection
    conn = db.engine.raw_connection()
    try:
        cursor = conn.cursor()

        # First, check if we need to rename the table
        try:
            cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_name='user' AND table_schema='public'
            """)

            if cursor.fetchone() and not table_exists(cursor, 'users'):
                print("Renaming 'user' table to 'users'...")
                cursor.execute("ALTER TABLE IF EXISTS \"user\" RENAME TO users")
                # Also update alembic_version to prevent future conflicts
                cursor.execute("UPDATE alembic_version SET version_num = 'add_missing_user_columns' WHERE version_num = '23258794272e'")
                print("Table renamed successfully")
        except Exception as e:
            print(f"Error checking/renaming table: {e}")

        # Check and add username column
        try:
            if not column_exists(cursor, 'users', 'username'):
                cursor.execute("ALTER TABLE users ADD COLUMN username VARCHAR(64)")
                cursor.execute("CREATE INDEX IF NOT EXISTS ix_users_username ON users (username)")
                print("Added username column")
            else:
                print("username column already exists")
        except Exception as e:
            print(f"Error adding username column: {e}")

        # Check and add authentik_id column
        try:
            if not column_exists(cursor, 'users', 'authentik_id'):
                cursor.execute("ALTER TABLE users ADD COLUMN authentik_id VARCHAR(64)")
                print("Added authentik_id column")
            else:
                print("authentik_id column already exists")
        except Exception as e:
            print(f"Error adding authentik_id column: {e}")

        # Check and add signal_identity column
        try:
            if not column_exists(cursor, 'users', 'signal_identity'):
                cursor.execute("ALTER TABLE users ADD COLUMN signal_identity VARCHAR(64)")
                print("Added signal_identity column")
            else:
                print("signal_identity column already exists")
        except Exception as e:
            print(f"Error adding signal_identity column: {e}")

        # Check and add attributes column
        try:
            if not column_exists(cursor, 'users', 'attributes'):
                cursor.execute("ALTER TABLE users ADD COLUMN attributes JSONB DEFAULT '{}'::jsonb")
                print("Added attributes column")
            else:
                print("attributes column already exists")
        except Exception as e:
            print(f"Error adding attributes column: {e}")

        # Check and add is_active column
        try:
            if not column_exists(cursor, 'users', 'is_active'):
                cursor.execute("ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT TRUE")
                print("Added is_active column")
            else:
                print("is_active column already exists")
        except Exception as e:
            print(f"Error adding is_active column: {e}")

        # Check and add is_admin column
        try:
            if not column_exists(cursor, 'users', 'is_admin'):
                cursor.execute("ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT FALSE")
                print("Added is_admin column")
            else:
                print("is_admin column already exists")
        except Exception as e:
            print(f"Error adding is_admin column: {e}")

        # Check and add date_joined column
        try:
            if not column_exists(cursor, 'users', 'date_joined'):
                cursor.execute("ALTER TABLE users ADD COLUMN date_joined TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
                # Copy data from created_at column
                cursor.execute("UPDATE users SET date_joined = created_at WHERE date_joined IS NULL")
                print("Added date_joined column")
            else:
                print("date_joined column already exists")
        except Exception as e:
            print(f"Error adding date_joined column: {e}")

        # Check and add last_login column
        try:
            if not column_exists(cursor, 'users', 'last_login'):
                cursor.execute("ALTER TABLE users ADD COLUMN last_login TIMESTAMP")
                print("Added last_login column")
            else:
                print("last_login column already exists")
        except Exception as e:
            print(f"Error adding last_login column: {e}")

        # Update foreign keys
        update_foreign_keys(cursor)

        # Commit all changes
        conn.commit()
        print("Committed all changes")

    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()

    print("User columns fix complete!")

def column_exists(cursor, table_name, column_name):
    """Helper to check if a column exists in the table"""
    cursor.execute(f"""
    SELECT column_name
    FROM information_schema.columns
    WHERE table_name='{table_name}' AND column_name='{column_name}'
    """)
    return cursor.fetchone() is not None

def table_exists(cursor, table_name):
    """Helper to check if a table exists"""
    cursor.execute(f"""
    SELECT table_name
    FROM information_schema.tables
    WHERE table_name='{table_name}' AND table_schema='public'
    """)
    return cursor.fetchone() is not None

def update_foreign_keys(cursor):
    """Update foreign keys that reference the user table"""
    try:
        # First check if user table was renamed to users
        cursor.execute("""
        SELECT constraint_name
        FROM information_schema.table_constraints
        WHERE constraint_type = 'FOREIGN KEY'
        AND table_schema = 'public'
        """)

        constraints = cursor.fetchall()

        for constraint in constraints:
            constraint_name = constraint[0]

            # Get the reference details for this constraint
            cursor.execute(f"""
            SELECT tc.table_name, kcu.column_name,
                   ccu.table_name AS foreign_table_name,
                   ccu.column_name AS foreign_column_name
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
              ON tc.constraint_name = kcu.constraint_name
            JOIN information_schema.constraint_column_usage AS ccu
              ON ccu.constraint_name = tc.constraint_name
            WHERE tc.constraint_name = '{constraint_name}'
            AND tc.constraint_type = 'FOREIGN KEY'
            """)

            ref = cursor.fetchone()
            if ref and ref[2] == 'user':  # If this constraint references the 'user' table
                source_table = ref[0]
                source_column = ref[1]
                target_column = ref[3]

                print(f"Updating foreign key {constraint_name} from {source_table}.{source_column} to users.{target_column}")

                # Drop the old constraint
                cursor.execute(f"ALTER TABLE {source_table} DROP CONSTRAINT {constraint_name}")

                # Create a new constraint pointing to the 'users' table
                new_constraint_name = f"fk_{source_table}_{source_column}_users"
                cursor.execute(f"""
                ALTER TABLE {source_table}
                ADD CONSTRAINT {new_constraint_name}
                FOREIGN KEY ({source_column})
                REFERENCES users({target_column})
                """)

                print(f"Updated constraint {constraint_name} to {new_constraint_name}")
    except Exception as e:
        print(f"Error updating foreign keys: {e}")
        # Continue anyway, don't let this stop the script

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        add_user_columns()