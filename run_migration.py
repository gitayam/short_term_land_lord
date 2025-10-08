#!/usr/bin/env python3
"""
Run database migration for booking requests
"""

from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    # Create all tables defined in models
    db.create_all()
    print("✓ Database tables created/updated successfully")
    
    # Add latitude and longitude columns if they don't exist
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
        print("✓ Coordinate columns migration completed")
        
    except Exception as e:
        print(f"✗ Error during coordinate migration: {e}")
        db.session.rollback()