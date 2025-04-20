#!/usr/bin/env python3
"""
This script fixes various database schema issues by adding missing columns to tables
and ensuring relationships work correctly.
"""

import os
import sys
from sqlalchemy import text, inspect

# Import the app creation function
from app import create_app, db

def fix_all_schemas():
    """Fix all database schemas with missing columns"""
    # Create app with the application factory
    app = create_app()
    
    with app.app_context():
        inspector = inspect(db.engine)
        
        print("Checking database tables...")
        tables = inspector.get_table_names()
        print(f"Found tables: {tables}")
        
        changes_made = False
        
        # Fix User.is_admin property issue
        try:
            print("Adding missing relationships to the User model...")
            from app.models import User, Property
            
            # Check if the User model has the 'properties' relationship
            if not hasattr(User, 'properties'):
                print("Adding 'properties' relationship to User model...")
                # We'll use a different backref name to avoid conflicts
                User.properties = db.relationship('Property', 
                                                 foreign_keys='Property.owner_id', 
                                                 lazy='dynamic',
                                                 overlaps="owned_properties")
                print("Added 'properties' relationship to User model.")
                changes_made = True
                
                # Now let's update the user model's is_property_owner to be a method, not a property
                # so it doesn't conflict with the check_admin() method
                if hasattr(User, 'is_property_owner'):
                    original_property = User.is_property_owner
                    delattr(User, 'is_property_owner')
                    
                    def is_property_owner_method(self):
                        """Check if the user has the property owner role."""
                        from app.models import UserRoles
                        return self.role == UserRoles.PROPERTY_OWNER.value
                    
                    User.is_property_owner = is_property_owner_method
                    print("Updated is_property_owner to be a method instead of a property")
                    changes_made = True
            
            # Run a test query to verify relationships
            test_user = User.query.first()
            if test_user:
                print(f"Test user: {test_user.get_full_name()}")
                try:
                    print(f"Testing properties relationship... properties count: {test_user.properties.count()}")
                except Exception as e:
                    print(f"Could not test properties relationship: {e}")
            else:
                print("No users found to test relationships.")
                
        except Exception as e:
            print(f"Error fixing User model: {str(e)}")
        
        # Fix TaskTemplate table if needed
        if 'task_template' in tables:
            # Check TaskTemplate columns
            columns = [col['name'] for col in inspector.get_columns('task_template')]
            print(f"Columns in task_template: {columns}")
            
            # Check for is_global column
            if 'is_global' not in columns:
                print("Adding is_global column to task_template table...")
                with db.engine.connect() as connection:
                    connection.execute(text("ALTER TABLE task_template ADD COLUMN is_global BOOLEAN DEFAULT FALSE"))
                    connection.commit()
                print("is_global column added successfully!")
                changes_made = True
            
            # Check for sequence_number column
            if 'sequence_number' not in columns:
                print("Adding sequence_number column to task_template table...")
                with db.engine.connect() as connection:
                    connection.execute(text("ALTER TABLE task_template ADD COLUMN sequence_number INTEGER DEFAULT 0"))
                    connection.commit()
                print("sequence_number column added successfully!")
                changes_made = True
            
            # Check for category column
            if 'category' not in columns:
                print("Adding category column to task_template table...")
                with db.engine.connect() as connection:
                    connection.execute(text("ALTER TABLE task_template ADD COLUMN category VARCHAR(50)"))
                    connection.commit()
                print("category column added successfully!")
                changes_made = True
        
        if not changes_made:
            print("All tables already have the required columns and relationships!")
        
        return changes_made

if __name__ == '__main__':
    try:
        result = fix_all_schemas()
        if result:
            print("Fixed database schemas successfully!")
        else:
            print("No changes needed for database schemas.")
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1) 