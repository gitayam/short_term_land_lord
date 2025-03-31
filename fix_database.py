#!/usr/bin/env python
"""
Database fix script for short_term_land_lord project.
This script fixes enum values in the database to match model definitions.
"""
import os
import sys
from pathlib import Path
import sqlalchemy as sa

# Add the parent directory to sys.path
parent_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(parent_dir))

from app import create_app, db
from app.models import TaskStatus, GuestReviewRating, SiteSettings

def fix_database():
    """Fix database issues with enums and tables"""
    print("Starting database fix...")
    
    # Check database type (SQLite or PostgreSQL)
    db_uri = db.engine.url
    db_type = db_uri.drivername
    print(f"Detected database type: {db_type}")
    
    # Fix site_settings table
    try:
        # First check if the table exists
        table_exists = False
        try:
            conn = db.engine.connect()
            if 'postgres' in db_type:
                result = conn.execute(sa.text("SELECT to_regclass('site_settings')"))
                table_exists = result.scalar() is not None
            else:
                result = conn.execute(sa.text("SELECT name FROM sqlite_master WHERE type='table' AND name='site_settings'"))
                table_exists = result.scalar() is not None
        except Exception as e:
            print(f"Error checking if site_settings table exists: {e}")
            
        if not table_exists:
            print("site_settings table doesn't exist, creating it...")
            
            try:
                if 'postgres' in db_type:
                    conn.execute(sa.text("""
                    CREATE TABLE site_settings (
                        key VARCHAR(64) PRIMARY KEY,
                        value TEXT,
                        description VARCHAR(255),
                        visible BOOLEAN DEFAULT TRUE,
                        created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
                    )
                    """))
                else:
                    conn.execute(sa.text("""
                    CREATE TABLE site_settings (
                        key VARCHAR(64) PRIMARY KEY,
                        value TEXT,
                        description VARCHAR(255),
                        visible BOOLEAN DEFAULT 1,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                    """))
                conn.commit()
                print("Created site_settings table")
            except Exception as e:
                print(f"Error creating site_settings table: {e}")
                conn.rollback()
            
        # Check if there are any settings in the table
        if SiteSettings.query.count() == 0:
            print("Creating default site settings...")
            settings = [
                SiteSettings(key='guest_reviews_enabled', value='true', description='Enable guest reviews', visible=True),
                SiteSettings(key='cleaning_checklist_enabled', value='true', description='Enable cleaning checklists', visible=True),
                SiteSettings(key='maintenance_requests_enabled', value='true', description='Enable maintenance requests', visible=True),
                SiteSettings(key='require_cleaning_videos', value='false', description='Require videos for cleaning sessions', visible=True),
            ]
            
            for setting in settings:
                db.session.add(setting)
            
            db.session.commit()
            print(f"Created {len(settings)} default site settings.")
        else:
            print("Site settings already exist.")
    except Exception as e:
        print(f"Error with site settings: {e}")
        db.session.rollback()
    
    if 'postgres' in db_type:
        # PostgreSQL fixes
        print("Applying PostgreSQL-specific fixes...")
        try:
            # Fix TaskStatus enum
            conn = db.engine.connect()
            trans = conn.begin()
            
            # Check if we have data in the task table
            task_count = conn.execute(sa.text("SELECT COUNT(*) FROM task")).scalar()
            if task_count > 0:
                print(f"Found {task_count} tasks, fixing status values...")
                
                # Create a temporary table to store task data
                conn.execute(sa.text("CREATE TABLE IF NOT EXISTS task_backup AS SELECT * FROM task"))
                
                # Update task status values to match enum
                conn.execute(sa.text("""
                UPDATE task SET status = CASE 
                    WHEN status = 'PENDING' THEN 'pending'
                    WHEN status = 'IN_PROGRESS' THEN 'in_progress'
                    WHEN status = 'COMPLETED' THEN 'completed'
                    ELSE status
                END
                """))
                
                # Check guest review table
                review_count = conn.execute(sa.text("SELECT COUNT(*) FROM guest_review")).scalar()
                if review_count > 0:
                    print(f"Found {review_count} guest reviews, fixing rating values...")
                    
                    # Create backup
                    conn.execute(sa.text("CREATE TABLE IF NOT EXISTS guest_review_backup AS SELECT * FROM guest_review"))
                    
                    # Update guest review rating values
                    conn.execute(sa.text("""
                    UPDATE guest_review SET rating = CASE 
                        WHEN rating = 'GOOD' THEN 'good'
                        WHEN rating = 'OK' THEN 'ok'
                        WHEN rating = 'BAD' THEN 'bad'
                        ELSE rating
                    END
                    """))
            
            trans.commit()
            print("PostgreSQL fixes applied successfully.")
            
        except Exception as e:
            print(f"Error applying PostgreSQL fixes: {e}")
            if 'trans' in locals() and trans is not None:
                trans.rollback()
    else:
        print("No PostgreSQL-specific fixes needed for SQLite database.")
    
    print("Database fix complete!")

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        fix_database() 