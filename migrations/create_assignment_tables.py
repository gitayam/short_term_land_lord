#!/usr/bin/env python3
"""
Create Assignment Tables Migration
Adds PropertyAssignment, UserManagerAssignment, and UserOwnerAssignment tables for role assignments
"""

import os
import sys

# Add the parent directory to the path so we can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from sqlalchemy import text

def create_assignment_tables():
    """Create the assignment tables"""
    app = create_app()
    
    with app.app_context():
        print("Creating assignment tables...")
        
        # PropertyAssignment table
        property_assignments_sql = """
        CREATE TABLE IF NOT EXISTS property_assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            property_id INTEGER NOT NULL,
            assigned_by INTEGER NOT NULL,
            role VARCHAR(50) NOT NULL,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT 1,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (property_id) REFERENCES property (id),
            FOREIGN KEY (assigned_by) REFERENCES users (id)
        );
        """
        
        # UserManagerAssignment table
        manager_assignments_sql = """
        CREATE TABLE IF NOT EXISTS user_manager_assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            manager_id INTEGER NOT NULL,
            assigned_by INTEGER NOT NULL,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT 1,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (manager_id) REFERENCES users (id),
            FOREIGN KEY (assigned_by) REFERENCES users (id)
        );
        """
        
        # UserOwnerAssignment table
        owner_assignments_sql = """
        CREATE TABLE IF NOT EXISTS user_owner_assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            manager_id INTEGER NOT NULL,
            owner_id INTEGER NOT NULL,
            assigned_by INTEGER NOT NULL,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT 1,
            FOREIGN KEY (manager_id) REFERENCES users (id),
            FOREIGN KEY (owner_id) REFERENCES users (id),
            FOREIGN KEY (assigned_by) REFERENCES users (id)
        );
        """
        
        try:
            # Execute the SQL
            db.session.execute(text(property_assignments_sql))
            print("✓ Created property_assignments table")
            
            db.session.execute(text(manager_assignments_sql))
            print("✓ Created user_manager_assignments table")
            
            db.session.execute(text(owner_assignments_sql))
            print("✓ Created user_owner_assignments table")
            
            # Create indexes for better performance
            indexes_sql = [
                "CREATE INDEX IF NOT EXISTS idx_property_assignments_user_id ON property_assignments(user_id);",
                "CREATE INDEX IF NOT EXISTS idx_property_assignments_property_id ON property_assignments(property_id);",
                "CREATE INDEX IF NOT EXISTS idx_property_assignments_role ON property_assignments(role);",
                "CREATE INDEX IF NOT EXISTS idx_manager_assignments_user_id ON user_manager_assignments(user_id);",
                "CREATE INDEX IF NOT EXISTS idx_manager_assignments_manager_id ON user_manager_assignments(manager_id);",
                "CREATE INDEX IF NOT EXISTS idx_owner_assignments_manager_id ON user_owner_assignments(manager_id);",
                "CREATE INDEX IF NOT EXISTS idx_owner_assignments_owner_id ON user_owner_assignments(owner_id);"
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
    create_assignment_tables()