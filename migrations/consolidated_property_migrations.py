#!/usr/bin/env python3
"""
Consolidated property table migrations script.
This script combines various property-related table migrations into a single script:
1. Creates the property table if it doesn't exist
2. Adds address component columns (street_address, city, state, etc.)
3. Adds property details columns (bedrooms, bathrooms, etc.)
4. Adds utility information columns
5. Adds other property-related columns

Usage:
    python consolidated_property_migrations.py
"""
import os
import sys
from pathlib import Path

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import text, inspect
from app import create_app, db

def ensure_property_table():
    """Ensure the property table exists with basic columns"""
    app = create_app()
    
    with app.app_context():
        inspector = inspect(db.engine)
        
        if 'property' not in inspector.get_table_names():
            print("Property table doesn't exist, creating it...")
            with db.engine.connect() as conn:
                with conn.begin():
                    conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS property (
                        id SERIAL PRIMARY KEY,
                        owner_id INTEGER NOT NULL,
                        name VARCHAR(128) NOT NULL,
                        address VARCHAR(256) NOT NULL,
                        description TEXT,
                        property_type VARCHAR(32) NOT NULL DEFAULT 'house',
                        status VARCHAR(20) DEFAULT 'active',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        guest_access_enabled BOOLEAN DEFAULT FALSE,
                        guest_access_token VARCHAR(64) UNIQUE,
                        guest_rules TEXT,
                        guest_checkin_instructions TEXT,
                        guest_checkout_instructions TEXT,
                        guest_wifi_instructions TEXT,
                        local_attractions TEXT,
                        emergency_contact TEXT,
                        guest_faq TEXT,
                        FOREIGN KEY (owner_id) REFERENCES users(id)
                    )
                    """))
            
            print("Property table created successfully!")
            return True
        else:
            print("Property table already exists")
            return False

def add_property_columns():
    """Add all necessary property columns if they don't exist"""
    app = create_app()
    
    with app.app_context():
        inspector = inspect(db.engine)
        
        if 'property' not in inspector.get_table_names():
            print("Property table does not exist, skipping migration")
            return False
        
        # Get existing columns
        columns = {col['name']: col for col in inspector.get_columns('property')}
        changes_made = False
        
        # All columns to add with their types
        columns_to_add = {
            # Address components
            'street_address': 'VARCHAR(128)',
            'city': 'VARCHAR(64)',
            'state': 'VARCHAR(64)',
            'zip_code': 'VARCHAR(16)',
            'country': 'VARCHAR(64)',
            
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
                            conn.execute(text(f"ALTER TABLE property ADD COLUMN {column_name} {column_type}"))
                        print(f"Added {column_name} column")
                        changes_made = True
                    except Exception as e:
                        print(f"Error adding {column_name} column: {e}")
        
        # Try to populate address components from address field if they were just added
        if changes_made and 'street_address' in columns_to_add and 'street_address' not in columns:
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
            print("Property columns added successfully!")
        else:
            print("All property columns already exist")
        
        return changes_made

def run_consolidated_property_migrations():
    """Run all property-related migrations in the correct order"""
    try:
        print("Starting consolidated property migrations...")
        
        # 1. Ensure property table exists
        ensure_property_table()
        
        # 2. Add all property-related columns
        add_property_columns()
        
        print("All property-related migrations completed successfully!")
        return True
        
    except Exception as e:
        print(f"Error in consolidated property migrations: {str(e)}")
        return False

if __name__ == '__main__':
    success = run_consolidated_property_migrations()
    sys.exit(0 if success else 1) 