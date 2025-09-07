#!/usr/bin/env python3
"""
This script fixes database schema issues related to testing,
particularly addressing enum-related SQLite compatibility issues.
"""

import os
import sys
import inspect
from sqlalchemy import text, inspect

# Import the app creation function
from app import create_app, db
from app.models import User, UserRoles, Task, TaskStatus, TaskPriority, RecurrencePattern

def fix_test_db_schema():
    """Create/fix test database schema for SQLite compatibility"""
    # Configure for testing
    from config import TestConfig
    app = create_app(TestConfig)
    
    with app.app_context():
        # First drop all tables to ensure a clean slate
        db.drop_all()
        
        # Create tables fresh
        db.create_all()
        
        # Patch enums in models
        print("Patching enum handling in models...")
        
        # Add hook for User model to handle enums on assignment
        original_setattr = User.__setattr__
        
        def patched_setattr(self, key, value):
            if key == 'role' and isinstance(value, UserRoles):
                # Convert enum to string value
                value = value.value
            original_setattr(self, key, value)
        
        User.__setattr__ = patched_setattr
        
        # Patch Task model to handle enum fields
        original_task_setattr = Task.__setattr__
        
        def patched_task_setattr(self, key, value):
            if key == 'status' and isinstance(value, TaskStatus):
                value = value.value
            elif key == 'priority' and isinstance(value, TaskPriority):
                value = value.value
            elif key == 'recurrence_pattern' and isinstance(value, RecurrencePattern):
                value = value.value
            original_task_setattr(self, key, value)
        
        Task.__setattr__ = patched_task_setattr
        
        print("Database schema fixed for testing!")
        return True

if __name__ == '__main__':
    try:
        result = fix_test_db_schema()
        if result:
            print("Successfully set up test database schema!")
        else:
            print("No changes needed for test database schema.")
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1) 