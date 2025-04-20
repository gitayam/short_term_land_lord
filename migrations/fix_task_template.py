#!/usr/bin/env python3
"""
This script fixes the task_template table schema by creating it if it doesn't exist,
or adding the missing columns if the table exists but columns are missing.
"""

import os
import sys
from sqlalchemy import text, inspect

# Import the app creation function
from app import create_app, db

def fix_task_template_table():
    """Create or fix the task_template table"""
    # Create app with the application factory
    app = create_app()
    
    with app.app_context():
        inspector = inspect(db.engine)
        
        print("Checking database tables...")
        tables = inspector.get_table_names()
        print(f"Found tables: {tables}")
        
        if 'task_template' not in tables:
            print("Creating task_template table...")
            # Create the task_template table using SQLAlchemy
            db.create_all()
            print("Table created successfully!")
            return True
        
        # Table exists, check if columns exist
        columns = [col['name'] for col in inspector.get_columns('task_template')]
        print(f"Columns in task_template: {columns}")
        
        changes_made = False
        
        # Check for is_global column
        if 'is_global' not in columns:
            print("Adding is_global column to task_template table...")
            # Add the is_global column
            with db.engine.connect() as connection:
                connection.execute(text("ALTER TABLE task_template ADD COLUMN is_global BOOLEAN DEFAULT FALSE"))
                connection.commit()
            print("is_global column added successfully!")
            changes_made = True
        
        # Check for sequence_number column
        if 'sequence_number' not in columns:
            print("Adding sequence_number column to task_template table...")
            # Add the sequence_number column
            with db.engine.connect() as connection:
                connection.execute(text("ALTER TABLE task_template ADD COLUMN sequence_number INTEGER DEFAULT 0"))
                connection.commit()
            print("sequence_number column added successfully!")
            changes_made = True
        
        # Check for category column
        if 'category' not in columns:
            print("Adding category column to task_template table...")
            # Add the category column
            with db.engine.connect() as connection:
                connection.execute(text("ALTER TABLE task_template ADD COLUMN category VARCHAR(50)"))
                connection.commit()
            print("category column added successfully!")
            changes_made = True
        
        if not changes_made:
            print("task_template table already has all required columns!")
        
        return changes_made

if __name__ == '__main__':
    try:
        result = fix_task_template_table()
        if result:
            print("Fixed task_template schema successfully!")
        else:
            print("No changes needed for task_template schema.")
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1) 