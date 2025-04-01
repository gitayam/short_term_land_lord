#!/usr/bin/env python
"""
Script to patch the application's __init__.py file to automatically fix the User model
table name discrepancy between PostgreSQL and SQLite.
"""
import os
from pathlib import Path

def patch_app_init():
    """
    Add the necessary import and function call to app/__init__.py
    to automatically patch the User model during app initialization.
    """
    # Get the full path to app/__init__.py
    app_dir = Path(__file__).resolve().parent / 'app'
    init_file = app_dir / '__init__.py'
    
    if not init_file.exists():
        print(f"Error: {init_file} does not exist!")
        return False
    
    # Read the current content
    with open(init_file, 'r') as f:
        content = f.read()
    
    # Check if the patch has already been applied
    if 'patch_user_model' in content:
        print("Patch already applied to app/__init__.py")
        return True
    
    # Find where to insert the import 
    import_lines = []
    for line in content.split('\n'):
        if line.startswith('import ') or line.startswith('from '):
            import_lines.append(line)
    
    # Find the create_app function
    if 'def create_app(' not in content:
        print("Could not find create_app function in app/__init__.py")
        return False
    
    # Prepare the patch
    user_model_import = "from app.user_model_fix import patch_user_model, patch_user_loader"
    
    # Find where to add the patch in the create_app function
    lines = content.split('\n')
    modified_lines = []
    in_create_app = False
    app_return_index = -1
    
    for i, line in enumerate(lines):
        modified_lines.append(line)
        
        if 'def create_app(' in line:
            in_create_app = True
        elif in_create_app and 'return app' in line:
            app_return_index = i
            
    if app_return_index == -1:
        print("Could not find 'return app' in create_app function")
        return False
    
    # Add the import at the top of the file
    top_imports_end = 0
    for i, line in enumerate(lines):
        if line.strip() and not (line.startswith('import ') or line.startswith('from ')):
            top_imports_end = i
            break
    
    modified_lines.insert(top_imports_end, user_model_import)
    
    # Add the patch call before 'return app'
    patch_lines = [
        "    # Patch User model to handle different table names in SQLite vs PostgreSQL",
        "    with app.app_context():",
        "        patch_user_model()",
        "        patch_user_loader()",
        ""
    ]
    
    for i, line in enumerate(patch_lines):
        modified_lines.insert(app_return_index + i, line)
    
    # Write the modified content back
    with open(init_file, 'w') as f:
        f.write('\n'.join(modified_lines))
    
    print(f"Successfully patched {init_file}")
    return True

if __name__ == "__main__":
    patch_app_init() 