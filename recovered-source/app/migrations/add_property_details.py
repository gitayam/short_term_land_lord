#!/usr/bin/env python3
"""
Add missing property details columns to the property table.
This script adds all missing property detail columns such as bedrooms, bathrooms, etc. to the property table.
"""

import os
import sys
from pathlib import Path

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import text, inspect
from app import create_app, db

def add_property_details_fields():
    """Add missing property detail columns to the property table if they don't exist"""
    app = create_app()
    
    with app.app_context():
        inspector = inspect(db.engine)
        
        print("Checking property table columns...")
        
        if 'property' not in inspector.get_table_names():
            print("Property table does not exist, skipping migration")
            return False
        
        columns = {col['name']: col for col in inspector.get_columns('property')}
        changes_made = False
        
        # List of columns to add with their types
        columns_to_add = {
            # Property details
            'bedrooms': 'INTEGER',
            'bathrooms': 'FLOAT',
            'square_feet': 'INTEGER',
            'year_built': 'INTEGER',
            'trash_day': 'VARCHAR(20)',
            'recycling_day': 'VARCHAR(20)',
            'recycling_notes': 'TEXT',
            
            # Utility information
            'internet_provider': 'VARCHAR(100)',
            'internet_account': 'VARCHAR(100)',
            'internet_contact': 'VARCHAR(100)',
            'electric_provider': 'VARCHAR(100)',
            'electric_account': 'VARCHAR(100)',
            'electric_contact': 'VARCHAR(100)',
            'water_provider': 'VARCHAR(100)',
            'water_account': 'VARCHAR(100)',
            'water_contact': 'VARCHAR(100)',
            'trash_provider': 'VARCHAR(100)',
            'trash_account': 'VARCHAR(100)',
            'trash_contact': 'VARCHAR(100)',
            
            # Access information
            'cleaning_supplies_location': 'TEXT',
            'wifi_network': 'VARCHAR(100)',
            'wifi_password': 'VARCHAR(100)',
            'special_instructions': 'TEXT',
            'entry_instructions': 'TEXT',
            
            # Cleaner-specific information
            'total_beds': 'INTEGER',
            'bed_sizes': 'VARCHAR(255)',
            'number_of_tvs': 'INTEGER',
            'number_of_showers': 'INTEGER',
            'number_of_tubs': 'INTEGER',
            
            # Calendar integration
            'ical_url': 'VARCHAR(500)',
            
            # Check-in/out times
            'checkin_time': 'VARCHAR(10)',
            'checkout_time': 'VARCHAR(10)',
        }
        
        # Add each column if it doesn't exist
        with db.engine.connect() as conn:
            for column_name, column_type in columns_to_add.items():
                if column_name not in columns:
                    print(f"Adding {column_name} column to property table...")
                    try:
                        with conn.begin():
                            # Use database-agnostic approach
                            if db.engine.dialect.name == 'postgresql':
                                conn.execute(text(f"ALTER TABLE property ADD COLUMN {column_name} {column_type}"))
                            else:  # SQLite
                                conn.execute(text(f"ALTER TABLE property ADD COLUMN {column_name} {column_type}"))
                        print(f"Added {column_name} column")
                        changes_made = True
                    except Exception as e:
                        print(f"Error adding {column_name} column: {e}")
        
        if changes_made:
            print("Property detail columns added successfully!")
        else:
            print("All property detail columns already exist")
        
        return changes_made

if __name__ == '__main__':
    try:
        result = add_property_details_fields()
        if result:
            print("Added property detail fields successfully!")
        else:
            print("No changes needed for property detail fields.")
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1) 