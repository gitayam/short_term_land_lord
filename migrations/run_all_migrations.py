#!/usr/bin/env python3
"""
Master migration script to run all consolidated migrations in the correct order.
This script intelligently determines which migrations need to be run based on
database state rather than running everything blindly.

Usage:
    python run_all_migrations.py [--reset]
"""
import os
import sys
import time
import logging
import argparse
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

def check_database_exists():
    """Check if the database has the required tables"""
    try:
        from app import create_app, db
        app = create_app()

        with app.app_context():
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()

            # Check for critical tables
            critical_tables = ['users', 'site_settings']
            missing_tables = [table for table in critical_tables if table not in tables]

            if missing_tables:
                logger.info(f"Missing critical tables: {', '.join(missing_tables)}")
                return False
            return True
    except Exception as e:
        logger.error(f"Error checking database state: {e}")
        return False

def reset_database():
    """Reset the database using reset_db.py"""
    try:
        logger.info("Resetting database with reset_db.py")
        from reset_db import reset_database
        success = reset_database()
        return success
    except Exception as e:
        logger.error(f"Error resetting database: {e}")
        return False

def run_migrations(args):
    """Run all migrations in the correct order, intelligently skipping when appropriate"""
    try:
        logger.info("Starting migration process")

        # Check if we need to reset the database
        db_exists = check_database_exists()
        if args.reset or not db_exists:
            if args.reset:
                logger.info("Database reset requested via command-line argument")
            else:
                logger.info("Critical tables missing, database needs initialization")

            success = reset_database()
            if not success:
                logger.error("Database reset failed! Cannot continue.")
                return False
            logger.info("Database reset completed successfully")

        # Track if any migrations were applied
        any_migrations_applied = False

        # 1. Run user-related migrations if needed
        logger.info("Checking user table migrations...")
        from consolidated_user_migrations import run_consolidated_migrations as run_user_migrations
        user_migrations_result = run_user_migrations()
        any_migrations_applied = any_migrations_applied or user_migrations_result

        # 2. Run property-related migrations if needed
        logger.info("Checking property table migrations...")
        from consolidated_property_migrations import run_consolidated_property_migrations
        property_migrations_result = run_consolidated_property_migrations()
        any_migrations_applied = any_migrations_applied or property_migrations_result

        # 3. Run all database fixes using our consolidated script
        if any_migrations_applied or args.force_fixes:
            logger.info("Running consolidated database fixes...")
            try:
                from consolidated_db_fixes import run_consolidated_db_fixes
                db_fixes_result = run_consolidated_db_fixes()

                if not db_fixes_result:
                    logger.warning("Some database fixes failed, but continuing with migrations")
            except Exception as e:
                logger.error(f"Error running consolidated database fixes: {e}")
                logger.warning("Continuing with migrations despite fix errors")

            # 4. Run specific fix for Property-Room relationships
            logger.info("Running Property-Room relationship fixes...")
            try:
                from fix_property_room_relationships import fix_property_room_relationships
                property_room_fix_result = fix_property_room_relationships()

                if not property_room_fix_result:
                    logger.warning("Property-Room relationship fix failed, but continuing with migrations")
            except Exception as e:
                logger.error(f"Error running Property-Room relationship fix: {e}")
                logger.warning("Continuing with migrations despite fix errors")
        else:
            logger.info("No migrations were applied and --force-fixes not specified, skipping database fixes")

        # 5. Run task tags migration
        logger.info("Adding task tags for workorder functionality...")
        try:
            from add_task_tags_column import add_tags_column, mark_existing_workorders
            add_tags_column()
            mark_existing_workorders()
            logger.info("Task tags migration completed successfully")
        except Exception as e:
            logger.error(f"Error running task tags migration: {e}")
            logger.warning("Continuing with migrations despite errors")

        logger.info("All migrations completed!")
        return True
    except Exception as e:
        logger.error(f"Error running migrations: {e}")
        return False

if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Run all migrations in the correct order")
    parser.add_argument('--reset', action='store_true', help='Reset the database before migrations')
    parser.add_argument('--force-fixes', action='store_true', help='Force running repair scripts even if no migrations were applied')
    args = parser.parse_args()

    try:
        success = run_migrations(args)
        if success:
            logger.info("All database migrations completed successfully!")
            sys.exit(0)
        else:
            logger.error("Migrations failed. Check the logs for details.")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Unhandled exception during migrations: {e}")
        sys.exit(1)