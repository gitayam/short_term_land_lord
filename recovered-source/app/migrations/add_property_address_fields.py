#!/usr/bin/env python3
"""
Add address component columns to the property table.
This script adds street_address, city, state, zip_code, and country columns to the property table.
"""

import os
import sys

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import text, inspect
from app import create_app, db

def add_property_address_fields():
    """Add address component columns to the property table if they don't exist"""
    app = create_app()
    
    with app.app_context():
        inspector = inspect(db.engine)
        
        print("Checking property table columns...")
        
        if 'property' not in inspector.get_table_names():
            print("Property table does not exist, skipping migration")
            return False
        
        columns = {col['name']: col for col in inspector.get_columns('property')}
        changes_made = False
        
        # Add street_address column
        if 'street_address' not in columns:
            print("Adding street_address column to property table...")
            with db.engine.connect() as conn:
                with conn.begin():
                    conn.execute(text("ALTER TABLE property ADD COLUMN street_address VARCHAR(128)"))
            print("Added street_address column")
            changes_made = True
        
        # Add city column
        if 'city' not in columns:
            print("Adding city column to property table...")
            with db.engine.connect() as conn:
                with conn.begin():
                    conn.execute(text("ALTER TABLE property ADD COLUMN city VARCHAR(64)"))
            print("Added city column")
            changes_made = True
        
        # Add state column
        if 'state' not in columns:
            print("Adding state column to property table...")
            with db.engine.connect() as conn:
                with conn.begin():
                    conn.execute(text("ALTER TABLE property ADD COLUMN state VARCHAR(64)"))
            print("Added state column")
            changes_made = True
        
        # Add zip_code column
        if 'zip_code' not in columns:
            print("Adding zip_code column to property table...")
            with db.engine.connect() as conn:
                with conn.begin():
                    conn.execute(text("ALTER TABLE property ADD COLUMN zip_code VARCHAR(16)"))
            print("Added zip_code column")
            changes_made = True
        
        # Add country column
        if 'country' not in columns:
            print("Adding country column to property table...")
            with db.engine.connect() as conn:
                with conn.begin():
                    conn.execute(text("ALTER TABLE property ADD COLUMN country VARCHAR(64)"))
            print("Added country column")
            changes_made = True
        
        # Try to populate the new columns with data from the address field
        if changes_made:
            try:
                print("Attempting to populate address components from address field...")
                with db.engine.connect() as conn:
                    with conn.begin():
                        # First, get all properties
                        result = conn.execute(text("SELECT id, address FROM property"))
                        properties = result.fetchall()
                        
                        for prop in properties:
                            prop_id = prop[0]
                            address = prop[1]
                            
                            # Simple parsing - split by commas and try to extract components
                            parts = address.split(',')
                            
                            street_address = parts[0].strip() if len(parts) > 0 else None
                            city = parts[1].strip() if len(parts) > 1 else None
                            
                            # If there are more parts, try to extract state and zip
                            state_zip = None
                            if len(parts) > 2:
                                state_zip = parts[2].strip()
                            
                            state = None
                            zip_code = None
                            if state_zip:
                                state_zip_parts = state_zip.split()
                                if len(state_zip_parts) > 0:
                                    state = state_zip_parts[0]
                                if len(state_zip_parts) > 1:
                                    zip_code = state_zip_parts[1]
                            
                            country = parts[3].strip() if len(parts) > 3 else 'United States'
                            
                            # Update the property with extracted components
                            update_query = text("""
                                UPDATE property 
                                SET street_address = :street_address,
                                    city = :city,
                                    state = :state,
                                    zip_code = :zip_code,
                                    country = :country
                                WHERE id = :id
                            """)
                            
                            conn.execute(update_query, {
                                'street_address': street_address,
                                'city': city,
                                'state': state,
                                'zip_code': zip_code,
                                'country': country,
                                'id': prop_id
                            })
                print("Address components populated successfully")
            except Exception as e:
                print(f"Error populating address components: {e}")
        
        if changes_made:
            print("Property address columns added successfully!")
        else:
            print("All property address columns already exist")
        
        return changes_made

if __name__ == '__main__':
    try:
        result = add_property_address_fields()
        if result:
            print("Added property address fields successfully!")
        else:
            print("No changes needed for property address fields.")
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1) 