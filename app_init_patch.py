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
    
    # Apply the patch using the patch file if it exists
    patch_file = app_dir / '__init__.py.patch'
    if patch_file.exists():
        print(f"Found patch file at {patch_file}, applying it...")
        try:
            with open(patch_file, 'r') as f:
                patch_content = f.read()
            
            # Extract the changes from the patch
            import_line = None
            patch_code = []
            
            for line in patch_content.split('\n'):
                if line.startswith('+from app.user_model_fix'):
                    import_line = line[1:]  # Remove the + prefix
                elif line.startswith('+    with app.app_context()'):
                    # Found the start of the patch code block
                    patch_code.append(line[1:])  # Remove the + prefix
                elif patch_code and line.startswith('+'):
                    patch_code.append(line[1:])  # Remove the + prefix
            
            # Add the import at the top of the file
            if import_line:
                # Find a good place to insert the import
                lines = content.split('\n')
                import_section_end = 0
                
                for i, line in enumerate(lines):
                    if line.strip() and not (line.startswith('import ') or line.startswith('from ')):
                        import_section_end = i
                        break
                
                lines.insert(import_section_end, import_line)
                content = '\n'.join(lines)
            
            # Add the patch code before 'return app'
            if patch_code:
                # Find the return app line
                return_app_index = content.find('return app')
                if return_app_index != -1:
                    # Find the start of the line
                    line_start = content.rfind('\n', 0, return_app_index) + 1
                    
                    # Insert the patch code
                    patch_code_str = '\n'.join(patch_code)
                    content = content[:line_start] + patch_code_str + '\n\n' + content[line_start:]
                else:
                    print("Could not find 'return app' in the file")
                    return False
            
            # Write the modified content back
            with open(init_file, 'w') as f:
                f.write(content)
            
            print(f"Successfully patched {init_file} using patch file")
            return True
        except Exception as e:
            print(f"Error applying patch: {e}")
            # Fall back to the manual patching method
    
    # Manual patching method as fallback
    print("Using manual patching method...")
    
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
    db_init_index = -1
    
    for i, line in enumerate(lines):
        modified_lines.append(line)
        
        if 'def create_app(' in line:
            in_create_app = True
        elif in_create_app and 'db.init_app(app)' in line:
            db_init_index = i
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
    
    # Add the patch call after db.init_app(app) if found, otherwise before return app
    insert_index = db_init_index + 1 if db_init_index != -1 else app_return_index
    
    patch_lines = [
        "",
        "    with app.app_context():",
        "        # Apply database compatibility fixes",
        "        patch_user_model()",
        "        patch_user_loader()",
        ""
    ]
    
    for i, line in enumerate(patch_lines):
        modified_lines.insert(insert_index + i, line)
    
    # Write the modified content back
    with open(init_file, 'w') as f:
        f.write('\n'.join(modified_lines))
    
    print(f"Successfully patched {init_file}")
    return True

if __name__ == "__main__":
    patch_app_init() 