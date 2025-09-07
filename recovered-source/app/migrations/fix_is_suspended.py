#!/usr/bin/env python3
"""
Migration script to fix is_suspended column in users table.
"""
import os
import sys
from pathlib import Path

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import text
from app import create_app, db

def fix_is_suspended_column():
    """Fix is_suspended column in users table"""
    app = create_app()
    
    with app.app_context():
        try:
            with db.engine.connect() as conn:
                with conn.begin():
                    if db.engine.url.drivername == 'postgresql':
                        # PostgreSQL specific code
                        conn.execute(text("""
                            DO $$ 
                            BEGIN
                                IF EXISTS (
                                    SELECT 1 
                                    FROM information_schema.columns 
                                    WHERE table_name = 'users' 
                                    AND column_name = 'is_suspended'
                                ) THEN
                                    ALTER TABLE users DROP COLUMN is_suspended;
                                END IF;
                            END $$;
                        """))
                        conn.execute(text("""
                            ALTER TABLE users ADD COLUMN is_suspended BOOLEAN DEFAULT FALSE;
                        """))
                    else:
                        # SQLite specific code
                        try:
                            conn.execute(text("""
                                ALTER TABLE users DROP COLUMN is_suspended;
                            """))
                        except:
                            # Column might not exist, which is fine
                            pass
                        conn.execute(text("""
                            ALTER TABLE users ADD COLUMN is_suspended BOOLEAN DEFAULT FALSE;
                        """))
            
            print("Successfully fixed is_suspended column")
            return True
        except Exception as e:
            print(f"Error fixing is_suspended column: {e}")
            return False

if __name__ == '__main__':
    success = fix_is_suspended_column()
    sys.exit(0 if success else 1) 