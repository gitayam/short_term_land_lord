#!/usr/bin/env python
"""
Fix foreign key constraints related to User table in the database.
This script directly modifies the database schema to ensure compatibility
between SQLite and PostgreSQL versions of the application.
"""
import os
import sys
from pathlib import Path

# Add the parent directory to sys.path
parent_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(parent_dir))

from app import create_app, db
from sqlalchemy import text, inspect
from app.user_model_fix import get_user_table_name, get_user_fk_target

def fix_sqlite_fk_constraints():
    """Fix SQLite FK constraints for the User table."""
    print("Fixing SQLite foreign key constraints for User table...")
    
    # Only proceed if we're using SQLite
    dialect = db.engine.dialect.name
    if dialect != 'sqlite':
        print(f"Detected {dialect} dialect - FK constraints fix not needed")
        return True
    
    try:
        # Get the inspector to examine the schema
        inspector = inspect(db.engine)
        
        # Get existing tables
        tables = inspector.get_table_names()
        print(f"Found tables: {tables}")
        
        # Check for inventory_catalog_item table
        if 'inventory_catalog_item' in tables:
            # For SQLite, we need to:
            # 1. Create a temporary table with the correct schema
            # 2. Copy all data to the temporary table
            # 3. Drop the original table
            # 4. Rename the temporary table to the original name
            
            # Get columns from existing table
            columns = inspector.get_columns('inventory_catalog_item')
            col_defs = []
            for col in columns:
                name = col['name']
                type_name = str(col['type'])
                nullable = '' if col['nullable'] else 'NOT NULL'
                default = f"DEFAULT {col['default']}" if col['default'] is not None else ''
                primary_key = 'PRIMARY KEY' if col.get('primary_key', False) else ''
                col_defs.append(f"{name} {type_name} {nullable} {default} {primary_key}".strip())
            
            # Create SQL statements
            create_temp_table = f"""
            CREATE TABLE inventory_catalog_item_temp (
                {', '.join(col_defs)}
            );
            """
            
            # Use new foreign key constraint
            create_fk = """
            ALTER TABLE inventory_catalog_item_temp 
            ADD CONSTRAINT fk_creator_id FOREIGN KEY (creator_id) REFERENCES user(id);
            """
            
            # Copy data
            copy_data = """
            INSERT INTO inventory_catalog_item_temp 
            SELECT * FROM inventory_catalog_item;
            """
            
            # Drop original
            drop_original = "DROP TABLE inventory_catalog_item;"
            
            # Rename temp
            rename_temp = "ALTER TABLE inventory_catalog_item_temp RENAME TO inventory_catalog_item;"
            
            # Execute the SQL statements
            with db.engine.begin() as conn:
                print("Creating temporary table...")
                conn.execute(text(create_temp_table))
                
                print("Adding foreign key constraint...")
                conn.execute(text(create_fk))
                
                print("Copying data...")
                conn.execute(text(copy_data))
                
                print("Dropping original table...")
                conn.execute(text(drop_original))
                
                print("Renaming temporary table...")
                conn.execute(text(rename_temp))
            
            print("inventory_catalog_item table FK constraints fixed!")
        
        # If there are other tables with FK to User, fix them here in a similar way
        
        print("All FK constraints fixed!")
        return True
    except Exception as e:
        print(f"Error fixing SQLite FK constraints: {e}")
        return False

def fix_postgresql_fk_constraints():
    """Fix PostgreSQL FK constraints for the User table."""
    print("Fixing PostgreSQL foreign key constraints for User table...")
    
    # Only proceed if we're using PostgreSQL
    dialect = db.engine.dialect.name
    if dialect != 'postgresql':
        print(f"Detected {dialect} dialect - PostgreSQL FK fix not needed")
        return True
    
    try:
        # Get correct table name
        user_table = get_user_table_name()  # Should be 'users' for PostgreSQL
        
        # Use SQL to update foreign key constraints
        update_fk_sql = f"""
        -- Drop existing FK constraints
        ALTER TABLE inventory_catalog_item 
        DROP CONSTRAINT IF EXISTS inventory_catalog_item_creator_id_fkey;
        
        -- Add new FK constraint
        ALTER TABLE inventory_catalog_item 
        ADD CONSTRAINT inventory_catalog_item_creator_id_fkey 
        FOREIGN KEY (creator_id) REFERENCES {user_table}(id);
        """
        
        # Execute SQL
        with db.engine.begin() as conn:
            print(f"Updating FK constraint to point to {user_table}...")
            conn.execute(text(update_fk_sql))
        
        print("PostgreSQL FK constraints fixed!")
        return True
    except Exception as e:
        print(f"Error fixing PostgreSQL FK constraints: {e}")
        return False

def fix_fk_constraints():
    """Main function to fix FK constraints based on current dialect."""
    # Get the database dialect
    dialect = db.engine.dialect.name
    print(f"Detected database dialect: {dialect}")
    
    if dialect == 'sqlite':
        return fix_sqlite_fk_constraints()
    elif dialect == 'postgresql':
        return fix_postgresql_fk_constraints()
    else:
        print(f"Unsupported dialect: {dialect}")
        return False

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        fix_fk_constraints() 