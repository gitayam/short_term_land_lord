#!/usr/bin/env python
"""
Direct patch for the User model to fix the table name discrepancy.

This script modifies the User model's __tablename__ attribute directly in the 
models.py file to use a dynamic table name based on the database dialect.
"""
import os
import re
from pathlib import Path

def patch_user_model_definition():
    """Find and patch the User model definition in models.py"""
    # Find the models.py file
    app_dir = Path(__file__).resolve().parent / 'app'
    models_file = app_dir / 'models.py'
    
    if not models_file.exists():
        print(f"Error: {models_file} does not exist!")
        return False
    
    print(f"Found models file at: {models_file}")
    
    # Read the current content
    with open(models_file, 'r') as f:
        content = f.read()
    
    # Check if the patch has already been applied
    if "get_user_table_name()" in content:
        print("User model already patched")
        return True
    
    # Add the helper function
    helper_function = """
def get_user_table_name():
    \"\"\"Returns the appropriate table name based on database dialect\"\"\"
    from app import db
    if db.engine.dialect.name == 'postgresql':
        return 'users'
    else:
        return 'user'
"""
    
    # Find the User class definition
    user_class_match = re.search(r'class User\([^)]+\):\s+', content)
    if not user_class_match:
        print("Could not find User class definition in models.py")
        return False
    
    # Find the __tablename__ line in the User class
    tablename_pattern = r'(__tablename__\s*=\s*[\'"]user[\'"])'
    tablename_match = re.search(tablename_pattern, content)
    
    if not tablename_match:
        # If not found, add it after the class definition
        print("Could not find __tablename__ in User class, will add it")
        user_class_end = user_class_match.end()
        
        # Add the helper function before the User class
        user_class_start = user_class_match.start()
        content = content[:user_class_start] + helper_function + content[user_class_start:]
        
        # Adjust the user_class_end to account for the added helper function
        user_class_end += len(helper_function)
        
        # Add the __tablename__ line after the class definition
        dynamic_tablename = "    __tablename__ = get_user_table_name()"
        content = content[:user_class_end] + dynamic_tablename + "\n" + content[user_class_end:]
    else:
        # Replace the existing __tablename__ line
        print("Found __tablename__ in User class, will replace it")
        
        # Add the helper function before the User class
        user_class_start = user_class_match.start()
        content = content[:user_class_start] + helper_function + content[user_class_start:]
        
        # Find the __tablename__ line again (position might have changed)
        tablename_match = re.search(tablename_pattern, content)
        if tablename_match:
            # Replace it with dynamic version
            dynamic_tablename = "__tablename__ = get_user_table_name()"
            content = content[:tablename_match.start(1)] + dynamic_tablename + content[tablename_match.end(1):]
    
    # Write the modified content back
    with open(models_file, 'w') as f:
        f.write(content)
    
    print(f"Successfully patched {models_file}")
    return True

def patch_user_loader():
    """Patch the user_loader function to handle table name differences"""
    # Find the models.py file
    app_dir = Path(__file__).resolve().parent / 'app'
    models_file = app_dir / 'models.py'
    
    if not models_file.exists():
        print(f"Error: {models_file} does not exist!")
        return False
    
    # Read the current content
    with open(models_file, 'r') as f:
        content = f.read()
    
    # Check if the load_user function is already patched
    if "get_user_table_name()" in content and "@login.user_loader" in content:
        # Check if it's already using direct SQL
        if "text(" in content and "execute(" in content:
            print("User loader already patched")
            return True
    
    # Find the load_user function
    loader_pattern = r'@login\.user_loader\s+def load_user\(([^)]+)\):[^r]*return User\.query\.get\('
    loader_match = re.search(loader_pattern, content)
    
    if not loader_match:
        print("Could not find load_user function in models.py")
        return False
    
    # Prepare the patched loader function
    param_name = loader_match.group(1).strip()
    patched_loader = f"""@login.user_loader
def load_user({param_name}):
    \"\"\"Load user by ID, handling different table names\"\"\"
    try:
        from sqlalchemy import text
        from app import db
        
        # Use direct SQL query with the correct table name
        table_name = get_user_table_name()
        sql = text(f"SELECT * FROM {{table_name}} WHERE id = :user_id")
        result = db.session.execute(sql, {{'user_id': int({param_name})}})
        row = result.fetchone()
        
        if row:
            # Create a User instance manually
            user = User()
            for key in row._mapping.keys():
                setattr(user, key, row._mapping[key])
            return user
        return None
    except Exception as e:
        import logging
        logging.error(f"Error in load_user: {{e}}")
        
        # Fallback to ORM
        try:
            return User.query.get(int({param_name}))
        except:
            return None
"""
    
    # Replace the old loader function
    content = re.sub(loader_pattern, patched_loader, content)
    
    # Write the modified content back
    with open(models_file, 'w') as f:
        f.write(content)
    
    print(f"Successfully patched load_user in {models_file}")
    return True

if __name__ == "__main__":
    # Patch the User model definition
    patch_user_model_definition()
    
    # Patch the user_loader function
    patch_user_loader() 