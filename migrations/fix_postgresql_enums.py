#!/usr/bin/env python
"""
PostgreSQL enum fix script for short_term_land_lord project.
This script ensures enum types exist in PostgreSQL before model classes try to use them.
"""
import sys
import os
from sqlalchemy import text, inspect
from sqlalchemy.exc import ProgrammingError

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import db, create_app
from app.models import TaskStatus, GuestReviewRating, RecurrencePattern, ServiceType
from config import Config

def fix_postgresql_enums():
    """Create PostgreSQL enum types if they don't exist."""
    print("Starting PostgreSQL enum fix...")
    
    # Only run this for PostgreSQL
    dialect = db.engine.dialect.name
    if dialect != 'postgresql':
        print(f"Skipping enum fix for {dialect} database")
        return
    
    # Check and create enums
    try:
        # Check if guestreviewrating enum type exists
        try:
            db.session.execute(text("SELECT 'BAD'::guestreviewrating"))
            print("guestreviewrating enum already exists")
        except ProgrammingError:
            print("guestreviewrating enum not found, creating it...")
            db.session.rollback()
            # Create the enum type
            db.session.execute(text("""
            CREATE TYPE guestreviewrating AS ENUM ('BAD', 'OK', 'GOOD')
            """))
            db.session.commit()
            print("Created guestreviewrating enum")
        
        # Check if taskstatus enum type exists
        try:
            db.session.execute(text("SELECT 'PENDING'::taskstatus"))
            print("taskstatus enum already exists")
        except ProgrammingError:
            print("taskstatus enum not found, creating it...")
            db.session.rollback()
            # Create the enum type
            db.session.execute(text("""
            CREATE TYPE taskstatus AS ENUM ('PENDING', 'IN_PROGRESS', 'COMPLETED')
            """))
            db.session.commit()
            print("Created taskstatus enum")
        
        # Check if servicetype enum exists
        try:
            db.session.execute(text("SELECT 'cleaning'::servicetype"))
            print("servicetype enum already exists")
        except ProgrammingError:
            print("servicetype enum not found, creating it...")
            db.session.rollback()
            # Create the enum type with all ServiceType values
            service_values = [s.value for s in ServiceType]
            values_str = "', '".join(service_values)
            db.session.execute(text(f"""
            CREATE TYPE servicetype AS ENUM ('{values_str}')
            """))
            db.session.commit()
            print("Created servicetype enum")
        
        # Check if recurrencepattern enum exists
        try:
            db.session.execute(text("SELECT 'none'::recurrencepattern"))
            print("recurrencepattern enum already exists")
        except ProgrammingError:
            print("recurrencepattern enum not found, creating it...")
            db.session.rollback()
            # Create the enum type with all RecurrencePattern values
            pattern_values = [p.value for p in RecurrencePattern]
            values_str = "', '".join(pattern_values)
            db.session.execute(text(f"""
            CREATE TYPE recurrencepattern AS ENUM ('{values_str}')
            """))
            db.session.commit()
            print("Created recurrencepattern enum")
        
        print("Committed all changes")
        
    except Exception as e:
        db.session.rollback()
        print(f"Error fixing PostgreSQL enums: {e}")
    
    print("PostgreSQL enum fix complete!")

if __name__ == "__main__":
    app = create_app(Config)
    with app.app_context():
        fix_postgresql_enums() 