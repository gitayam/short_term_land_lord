#!/usr/bin/env python3
"""
Master migration script to run all consolidated migrations in the correct order.
This script ensures that all database tables are created and properly configured.

Usage:
    python run_all_migrations.py
"""
import os
import sys
import time
import logging
from pathlib import Path
from dotenv import load_dotenv

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load environment variables from .env file
env_path = Path(os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))) / '.env'
load_dotenv(dotenv_path=env_path)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('migrations')

def run_migrations():
    """Run all migrations in the correct order"""
    try:
        logger.info("Starting all migrations")
        
        # 1. Run user-related migrations
        logger.info("Running user table migrations...")
        from consolidated_user_migrations import run_consolidated_migrations as run_user_migrations
        if not run_user_migrations():
            logger.error("User migrations failed!")
            return False
        
        # 2. Run property-related migrations
        logger.info("Running property table migrations...")
        from consolidated_property_migrations import run_consolidated_property_migrations
        if not run_consolidated_property_migrations():
            logger.error("Property migrations failed!")
            return False
        
        # 3. Run any other necessary migrations here
        # [Add additional migration calls as needed]
        
        # 4. Run any database fixes
        try:
            logger.info("Running database fixes...")
            
            from fix_fk_constraints import fix_foreign_keys
            logger.info("Fixing foreign key constraints...")
            fix_foreign_keys()
            
            from fix_postgres_schema import fix_postgres_schema
            logger.info("Fixing PostgreSQL schema issues...")
            fix_postgres_schema()
            
            from fix_task_template import fix_task_templates
            logger.info("Fixing task templates...")
            fix_task_templates()
            
            from fix_inventory_models import fix_inventory_models
            logger.info("Fixing inventory models...")
            fix_inventory_models()
            
            from initialize_task_templates import initialize_templates
            logger.info("Initializing task templates...")
            initialize_templates()
            
            from fix_site_settings import fix_site_settings
            logger.info("Fixing site settings...")
            fix_site_settings()
        except Exception as e:
            logger.error(f"Error running database fixes: {e}")
            logger.warning("Continuing with migrations despite fix errors")
        
        logger.info("All migrations completed successfully!")
        return True
    except Exception as e:
        logger.error(f"Error running migrations: {e}")
        return False

if __name__ == "__main__":
    try:
        success = run_migrations()
        if success:
            logger.info("All database migrations completed successfully!")
            sys.exit(0)
        else:
            logger.error("Migrations failed. Check the logs for details.")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Unhandled exception during migrations: {e}")
        sys.exit(1) 