#!/usr/bin/env python3
"""
Create PostgreSQL database schema for Short Term Landlord
Run this before migrating data from SQLite
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db

# Use PostgreSQL configuration
os.environ['FLASK_ENV'] = 'postgres_dev'

def create_schema():
    """Create all tables in PostgreSQL database"""
    
    # Create app with PostgreSQL config
    app = create_app('postgres_dev')
    
    with app.app_context():
        # Drop all existing tables (careful!)
        print("Dropping existing tables...")
        db.drop_all()
        
        # Create all tables
        print("Creating database schema...")
        db.create_all()
        
        # Verify tables were created
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        
        print(f"\n✅ Successfully created {len(tables)} tables:")
        for table in sorted(tables):
            print(f"  - {table}")
        
        return tables

if __name__ == "__main__":
    try:
        tables = create_schema()
        print(f"\n✅ Schema creation complete! Ready for data migration.")
    except Exception as e:
        print(f"\n❌ Schema creation failed: {e}")
        sys.exit(1)