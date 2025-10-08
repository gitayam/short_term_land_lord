#!/usr/bin/env python3
"""
Add latitude and longitude columns to property table
"""

import os
import sys

# Add the parent directory to the path so we can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from sqlalchemy import text

def add_property_coordinates():
    """Add the latitude and longitude columns to property table"""
    app = create_app()
    
    with app.app_context():
        print("Adding latitude and longitude columns to property table...")
        
        try:
            # Check if columns already exist
            check_lat_sql = """
            SELECT COUNT(*) as count 
            FROM pragma_table_info('property') 
            WHERE name='latitude';
            """
            result_lat = db.session.execute(text(check_lat_sql)).first()
            
            check_lng_sql = """
            SELECT COUNT(*) as count 
            FROM pragma_table_info('property') 
            WHERE name='longitude';
            """
            result_lng = db.session.execute(text(check_lng_sql)).first()
            
            if result_lat and result_lat.count > 0:
                print("✓ Column latitude already exists")
            else:
                # Add the latitude column
                alter_lat_sql = "ALTER TABLE property ADD COLUMN latitude REAL;"
                db.session.execute(text(alter_lat_sql))
                print("✓ Added latitude column")
            
            if result_lng and result_lng.count > 0:
                print("✓ Column longitude already exists")
            else:
                # Add the longitude column
                alter_lng_sql = "ALTER TABLE property ADD COLUMN longitude REAL;"
                db.session.execute(text(alter_lng_sql))
                print("✓ Added longitude column")
            
            # Commit all changes
            db.session.commit()
            print("✓ Migration completed successfully")
            
        except Exception as e:
            print(f"✗ Error during migration: {e}")
            db.session.rollback()
            raise
            
        finally:
            db.session.close()

if __name__ == '__main__':
    add_property_coordinates()