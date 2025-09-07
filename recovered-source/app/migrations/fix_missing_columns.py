#!/usr/bin/env python3
"""
Migration script to fix missing columns in the database.
This script checks for missing columns in the database schema and adds them 
if they don't exist, preventing SQLAlchemy errors from model-table mismatch.
"""

import os
import sys
import logging
from sqlalchemy import create_engine, inspect, text

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('fix_missing_columns')

def fix_missing_columns():
    """Check and add missing columns to database tables"""
    database_url = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@db/flask_app")
    logger.info(f"Using database URL: {database_url}")
    
    try:
        engine = create_engine(database_url)
        with engine.connect() as conn:
            inspector = inspect(engine)
            
            # Fix users table
            if 'users' in inspector.get_table_names():
                logger.info("Checking users table for missing columns...")
                user_columns = inspector.get_columns('users')
                column_names = [col['name'] for col in user_columns]
                
                # Check for authentik_id
                if 'authentik_id' not in column_names:
                    logger.info("Adding authentik_id column to users table")
                    conn.execute(text("ALTER TABLE users ADD COLUMN authentik_id VARCHAR(64)"))
                
                # Check for signal_identity
                if 'signal_identity' not in column_names:
                    logger.info("Adding signal_identity column to users table")
                    conn.execute(text("ALTER TABLE users ADD COLUMN signal_identity VARCHAR(64)"))
                
                # Check for attributes
                if 'attributes' not in column_names:
                    logger.info("Adding attributes column to users table")
                    conn.execute(text("ALTER TABLE users ADD COLUMN attributes JSONB"))
                
                # Make sure there are no pending transactions
                conn.execute(text("COMMIT"))
                logger.info("Users table columns updated successfully")
            else:
                logger.warning("Users table not found. Schema may need to be created first.")
            
            # Check site_settings table
            if 'site_settings' in inspector.get_table_names():
                logger.info("Checking site_settings table for required settings...")
                
                # Add any missing site settings
                conn.execute(text("""
                    INSERT INTO site_settings (key, value, description, visible)
                    VALUES 
                        ('app_name', 'Property Management', 'Application Name', TRUE),
                        ('guest_reviews_enabled', 'True', 'Enable guest reviews', TRUE),
                        ('cleaning_checklist_enabled', 'True', 'Enable cleaning checklists', TRUE),
                        ('maintenance_requests_enabled', 'True', 'Enable maintenance requests', TRUE)
                    ON CONFLICT (key) DO NOTHING
                """))
                
                # Commit changes
                conn.execute(text("COMMIT"))
                logger.info("Site settings table updated")
                
            return True
            
    except Exception as e:
        logger.error(f"Error fixing missing columns: {e}")
        return False

if __name__ == "__main__":
    logger.info("Running fix_missing_columns script...")
    success = fix_missing_columns()
    if success:
        logger.info("All missing columns have been added")
        sys.exit(0)
    else:
        logger.error("Failed to fix missing columns")
        sys.exit(1) 