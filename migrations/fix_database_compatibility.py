#!/usr/bin/env python
"""
Comprehensive database compatibility fix script.

This script applies all necessary fixes to ensure the application works correctly
with both PostgreSQL and SQLite databases:
1. Fixes the User model to use the correct table name ('users' for PostgreSQL, 'user' for SQLite)
2. Fixes PostgreSQL enum values to use lowercase instead of uppercase
3. Applies the user_loader fix to handle different table names
4. Patches app/__init__.py to automatically apply these fixes on startup

Usage:
    python fix_database_compatibility.py
"""
import os
import sys
from pathlib import Path
import shutil

# Add the parent directory to sys.path
parent_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(parent_dir))

from app import create_app, db
from model_fix import fix_user_model, apply_login_manager_fix
from fix_postgresql_enums import fix_postgresql_enums
from app_init_patch import patch_app_init

def fix_database_compatibility():
    """Apply all database compatibility fixes"""
    print("Starting database compatibility fixes...")
    
    # Create a Flask app context
    app = create_app()
    
    with app.app_context():
        # Step 1: Fix the User model table name
        print("\n=== Fixing User model table name ===")
        fix_user_model()
        
        # Step 2: Fix PostgreSQL enum values
        print("\n=== Fixing PostgreSQL enum values ===")
        fix_postgresql_enums()
        
        # Step 3: Fix the login_manager user_loader
        print("\n=== Fixing login_manager user_loader ===")
        apply_login_manager_fix()
    
    # Step 4: Patch app/__init__.py to automatically apply fixes on startup
    print("\n=== Patching app/__init__.py ===")
    
    # First, create a backup of the original file
    app_init_file = parent_dir / 'app' / '__init__.py'
    backup_file = parent_dir / 'app' / '__init__.py.bak'
    
    if not backup_file.exists():
        print(f"Creating backup of {app_init_file} to {backup_file}")
        shutil.copy2(app_init_file, backup_file)
    
    # Apply the patch
    patch_app_init()
    
    print("\nAll database compatibility fixes have been applied!")
    print("The application should now work correctly with both PostgreSQL and SQLite databases.")
    print("\nIf you encounter any issues, you can restore the original app/__init__.py from the backup at:")
    print(f"  {backup_file}")

if __name__ == "__main__":
    fix_database_compatibility()
