#!/usr/bin/env python3

from app import create_app, db
from config import Config
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import ENUM

def fix_enum_sync():
    app = create_app(Config)
    with app.app_context():
        # Get the current enum values from the database
        result = db.session.execute(text("""
            SELECT enumlabel 
            FROM pg_enum 
            WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'servicetype')
            ORDER BY enumsortorder;
        """))
        
        db_values = [row[0] for row in result]
        print(f"Database enum values: {db_values}")
        
        # Check if there are any existing records with the problematic value
        result = db.session.execute(text("""
            SELECT DISTINCT service_type 
            FROM task_assignment 
            WHERE service_type = 'general_maintenance';
        """))
        
        existing_records = result.fetchall()
        print(f"Existing records with 'general_maintenance': {len(existing_records)}")
        
        if existing_records:
            print("Found existing records with 'general_maintenance' value")
            print("This confirms the database has the value but SQLAlchemy doesn't recognize it")
        
        # Try to refresh the enum type by recreating it
        try:
            # Drop and recreate the enum type with all values
            db.session.execute(text("""
                -- Create a new enum type with all values
                CREATE TYPE servicetype_new AS ENUM (
                    'cleaning', 'handyman', 'lawn_care', 'pool_maintenance', 
                    'general_maintenance', 'other'
                );
            """))
            
            # Update existing columns to use the new enum type
            db.session.execute(text("""
                ALTER TABLE task_assignment 
                ALTER COLUMN service_type TYPE servicetype_new 
                USING service_type::text::servicetype_new;
            """))
            
            db.session.execute(text("""
                ALTER TABLE task_template 
                ALTER COLUMN service_type TYPE servicetype_new 
                USING service_type::text::servicetype_new;
            """))
            
            # Drop the old enum type and rename the new one
            db.session.execute(text("DROP TYPE servicetype;"))
            db.session.execute(text("ALTER TYPE servicetype_new RENAME TO servicetype;"))
            
            db.session.commit()
            print("Successfully recreated the enum type")
            
        except Exception as e:
            print(f"Error recreating enum: {e}")
            db.session.rollback()
            
            # Alternative approach: just ensure the value exists
            try:
                db.session.execute(text("""
                    ALTER TYPE servicetype ADD VALUE IF NOT EXISTS 'general_maintenance';
                """))
                db.session.commit()
                print("Added 'general_maintenance' to existing enum type")
            except Exception as e2:
                print(f"Error adding value to enum: {e2}")
                db.session.rollback()

if __name__ == '__main__':
    fix_enum_sync() 