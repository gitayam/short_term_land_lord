#!/usr/bin/env python3
"""
Create User Management Tables Migration
Adds UserNote and UserAccountAction tables for comprehensive admin user management
"""

import os
import sys

# Add the parent directory to the path so we can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from sqlalchemy import text

def create_user_management_tables():
    """Create the user management tables"""
    app = create_app()
    
    with app.app_context():
        print("Creating user management tables...")
        
        # UserNote table
        user_notes_sql = """
        CREATE TABLE IF NOT EXISTS user_notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            admin_id INTEGER NOT NULL,
            note_type VARCHAR(50) NOT NULL DEFAULT 'general',
            content TEXT NOT NULL,
            is_important BOOLEAN DEFAULT 0,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (admin_id) REFERENCES users (id)
        );
        """
        
        # UserAccountAction table
        user_actions_sql = """
        CREATE TABLE IF NOT EXISTS user_account_actions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            admin_id INTEGER NOT NULL,
            action_type VARCHAR(50) NOT NULL,
            old_value VARCHAR(255),
            new_value VARCHAR(255),
            reason TEXT,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (admin_id) REFERENCES users (id)
        );
        """
        
        try:
            # Execute the SQL
            db.session.execute(text(user_notes_sql))
            print("✓ Created user_notes table")
            
            db.session.execute(text(user_actions_sql))
            print("✓ Created user_account_actions table")
            
            # Create indexes for better performance
            indexes_sql = [
                "CREATE INDEX IF NOT EXISTS idx_user_notes_user_id ON user_notes(user_id);",
                "CREATE INDEX IF NOT EXISTS idx_user_notes_admin_id ON user_notes(admin_id);",
                "CREATE INDEX IF NOT EXISTS idx_user_notes_created_at ON user_notes(created_at);",
                "CREATE INDEX IF NOT EXISTS idx_user_actions_user_id ON user_account_actions(user_id);",
                "CREATE INDEX IF NOT EXISTS idx_user_actions_admin_id ON user_account_actions(admin_id);",
                "CREATE INDEX IF NOT EXISTS idx_user_actions_created_at ON user_account_actions(created_at);",
                "CREATE INDEX IF NOT EXISTS idx_user_actions_action_type ON user_account_actions(action_type);"
            ]
            
            for index_sql in indexes_sql:
                db.session.execute(text(index_sql))
            
            print("✓ Created indexes")
            
            # Commit all changes
            db.session.commit()
            print("✓ Migration completed successfully")
            
        except Exception as e:
            print(f"✗ Error during migration: {e}")
            db.session.rollback()
            raise
            
        finally:
            db.session.close()

if __name__ == '__main__':
    create_user_management_tables()