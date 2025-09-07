#!/usr/bin/env python3
"""
Add booking calendar fields to property table
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import Property
from sqlalchemy import text

def add_booking_calendar_fields():
    """Add booking calendar fields to property table"""
    app = create_app()
    
    with app.app_context():
        try:
            # Add booking_calendar_token column
            db.session.execute(text("""
                ALTER TABLE property 
                ADD COLUMN IF NOT EXISTS booking_calendar_token VARCHAR(64) UNIQUE
            """))
            
            # Add booking_calendar_enabled column
            db.session.execute(text("""
                ALTER TABLE property 
                ADD COLUMN IF NOT EXISTS booking_calendar_enabled BOOLEAN DEFAULT FALSE
            """))
            
            db.session.commit()
            print("✓ Added booking calendar fields to property table")
            
        except Exception as e:
            db.session.rollback()
            print(f"✗ Error adding booking calendar fields: {e}")
            return False
    
    return True

if __name__ == "__main__":
    success = add_booking_calendar_fields()
    if success:
        print("Migration completed successfully!")
    else:
        print("Migration failed!")
        sys.exit(1) 