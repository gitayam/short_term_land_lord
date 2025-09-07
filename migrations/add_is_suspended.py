#!/usr/bin/env python3
"""
Migration script to add is_suspended column to users table.
"""
import os
import sys
from pathlib import Path

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import text
from app import create_app, db

def add_is_suspended_column():
    """Add is_suspended column to users table if it doesn't exist"""
    app = create_app()
    
    with app.app_context():
        inspector = db.inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('users')]
        
        if 'is_suspended' not in columns:
            print("Adding is_suspended column to users table...")
            with db.engine.connect() as conn:
                with conn.begin():
                    # For PostgreSQL, we need to check if the column exists first
                    if db.engine.url.drivername == 'postgresql':
                        conn.execute(text("""
                            DO $$ 
                            BEGIN
                                IF NOT EXISTS (
                                    SELECT 1 
                                    FROM information_schema.columns 
                                    WHERE table_name = 'users' 
                                    AND column_name = 'is_suspended'
                                ) THEN
                                    ALTER TABLE users ADD COLUMN is_suspended BOOLEAN DEFAULT FALSE;
                                END IF;
                            END $$;
                        """))
                    else:
                        # For SQLite and other databases
                        conn.execute(text("""
                            ALTER TABLE users 
                            ADD COLUMN IF NOT EXISTS is_suspended BOOLEAN DEFAULT FALSE
                        """))
            print("Added is_suspended column successfully")
            return True
        else:
            print("is_suspended column already exists")
            return False

if __name__ == '__main__':
    success = add_is_suspended_column()
    sys.exit(0 if success else 1) 