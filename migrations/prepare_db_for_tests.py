#!/usr/bin/env python3
"""
Database preparation script for test environments.
This ensures a clean, properly configured database before running tests.
"""

import os
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test_db_prep')

# Import our shared database preparation functions
from startup import (
    wait_for_postgres, 
    reset_postgres_transactions, 
    setup_flask_app, 
    fix_database_schema
)

def prepare_test_database():
    """Prepare database specifically for test environment"""
    logger.info("Preparing database for test environment...")
    
    # Set test-specific environment variables
    os.environ['FLASK_ENV'] = 'testing'
    if 'DATABASE_URL' not in os.environ:
        # Use the same database but with a test_ prefix
        if 'POSTGRES_DB' in os.environ:
            test_db = f"test_{os.environ['POSTGRES_DB']}"
        else:
            test_db = 'test_flask_app'
        os.environ['POSTGRES_DB'] = test_db
    
    try:
        # Connect to PostgreSQL and wait for it to be available
        postgres_ready, config = wait_for_postgres()
        if not postgres_ready:
            logger.error("PostgreSQL not available for tests. Exiting.")
            return False
        
        # Reset any problematic transactions
        reset_result = reset_postgres_transactions(config['url'])
        if not reset_result:
            logger.warning("Transaction reset failed. Tests may encounter issues.")
        
        # Set up minimal Flask app for database operations
        app = setup_flask_app(config['url'])
        
        # Fix database schema if needed
        schema_result = fix_database_schema(app)
        if not schema_result:
            logger.warning("Schema fixes failed. Tests may encounter issues.")
        
        # Run any test-specific database setup here
        with app.app_context():
            try:
                from app import db
                
                # Ensure tables are created
                logger.info("Creating/updating database tables for tests...")
                db.create_all()
                
                logger.info("Test database preparation completed successfully!")
                return True
            except Exception as e:
                logger.error(f"Error creating database tables: {e}")
                return False
    except Exception as e:
        logger.error(f"Unexpected error during test database preparation: {str(e)}")
        return False

if __name__ == "__main__":
    success = prepare_test_database()
    sys.exit(0 if success else 1) 