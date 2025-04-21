#!/usr/bin/env python3
"""
Database preparation and fix script for Flask application startup.
This script ensures all necessary database fixes are applied before the main application starts.
It works in both Docker and local development environments.
"""

import os
import sys
import time
import socket
import psycopg2
from sqlalchemy import create_engine, text
from flask import Flask
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('db_startup')

def is_docker():
    """Check if we're running in a Docker container"""
    try:
        with open('/proc/self/cgroup', 'r') as f:
            return 'docker' in f.read()
    except:
        # Path doesn't exist or can't be read, probably not in Docker
        return False

def is_host_available(host, port=5432, timeout=1):
    """Check if a host is available by attempting to connect to it"""
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except:
        return False

def get_postgres_config():
    """Get PostgreSQL connection parameters based on environment"""
    # Default Docker configuration
    config = {
        'host': 'db',
        'port': 5432,
        'user': 'postgres',
        'password': 'postgres',
        'dbname': 'flask_app'
    }

    # If we're not in Docker, try localhost
    if not is_docker() and not is_host_available('db', 5432):
        logger.info("Not running in Docker or 'db' host not found. Using localhost.")
        config['host'] = 'localhost'

        # Check for local PostgreSQL port (standard 5432 or 5434 as specified in docker-compose)
        if is_host_available('localhost', 5434):
            config['port'] = 5434
            logger.info("PostgreSQL detected on localhost:5434")
        elif is_host_available('localhost', 5432):
            logger.info("PostgreSQL detected on localhost:5432")

    # Override with environment variables if available
    if 'POSTGRES_HOST' in os.environ:
        config['host'] = os.environ['POSTGRES_HOST']
    if 'POSTGRES_PORT' in os.environ:
        config['port'] = int(os.environ['POSTGRES_PORT'])
    if 'POSTGRES_USER' in os.environ:
        config['user'] = os.environ['POSTGRES_USER']
    if 'POSTGRES_PASSWORD' in os.environ:
        config['password'] = os.environ['POSTGRES_PASSWORD']
    if 'POSTGRES_DB' in os.environ:
        config['dbname'] = os.environ['POSTGRES_DB']

    # Construct database URL
    db_url = f"postgresql://{config['user']}:{config['password']}@{config['host']}:{config['port']}/{config['dbname']}"

    # Use DATABASE_URL if provided
    config['url'] = os.environ.get('DATABASE_URL', db_url)

    return config

def wait_for_postgres(max_retries=30):
    """Wait for PostgreSQL to be available"""
    config = get_postgres_config()
    logger.info(f"Waiting for PostgreSQL at {config['host']}:{config['port']}...")

    retries = 0
    while retries < max_retries:
        try:
            conn = psycopg2.connect(
                host=config['host'],
                port=config['port'],
                user=config['user'],
                password=config['password'],
                dbname=config['dbname']
            )
            conn.close()
            logger.info("PostgreSQL is available!")
            return True, config
        except psycopg2.OperationalError as e:
            retries += 1
            logger.info(f"PostgreSQL not available yet. Retry {retries}/{max_retries}... ({str(e)})")
            time.sleep(1)

    logger.error(f"Could not connect to PostgreSQL after {max_retries} retries")
    return False, config

def reset_postgres_transactions(database_url):
    """Reset any problematic PostgreSQL transactions"""
    logger.info("Resetting any problematic PostgreSQL transactions...")

    try:
        # Create a direct connection to PostgreSQL with autocommit
        engine = create_engine(database_url)
        with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            # Find connections in an aborted state
            result = conn.execute(text("""
                SELECT pid, state
                FROM pg_stat_activity
                WHERE state = 'idle in transaction' OR
                      state = 'idle in transaction (aborted)' OR
                      state = 'active'
            """))

            transactions = result.fetchall()

            if transactions:
                logger.info(f"Found {len(transactions)} potentially problematic transactions. Resetting them...")
                for tx in transactions:
                    # Don't terminate our own connection
                    if tx.state != 'active':
                        try:
                            conn.execute(text(f"SELECT pg_terminate_backend({tx.pid})"))
                            logger.info(f"Terminated connection {tx.pid} in state {tx.state}")
                        except Exception as e:
                            logger.warning(f"Could not terminate connection {tx.pid}: {str(e)}")
            else:
                logger.info("No problematic transactions found.")

            # Check for any transaction locks
            logger.info("Checking for transaction locks...")
            result = conn.execute(text("""
                SELECT blocked_locks.pid AS blocked_pid,
                       blocking_locks.pid AS blocking_pid
                FROM pg_catalog.pg_locks blocked_locks
                JOIN pg_catalog.pg_stat_activity blocked_activity ON blocked_activity.pid = blocked_locks.pid
                JOIN pg_catalog.pg_locks blocking_locks
                    ON blocking_locks.locktype = blocked_locks.locktype
                    AND blocking_locks.database IS NOT DISTINCT FROM blocked_locks.database
                    AND blocking_locks.relation IS NOT DISTINCT FROM blocked_locks.relation
                    AND blocking_locks.page IS NOT DISTINCT FROM blocked_locks.page
                    AND blocking_locks.tuple IS NOT DISTINCT FROM blocked_locks.tuple
                    AND blocking_locks.virtualxid IS NOT DISTINCT FROM blocked_locks.virtualxid
                    AND blocking_locks.transactionid IS NOT DISTINCT FROM blocked_locks.transactionid
                    AND blocking_locks.classid IS NOT DISTINCT FROM blocked_locks.classid
                    AND blocking_locks.objid IS NOT DISTINCT FROM blocked_locks.objid
                    AND blocking_locks.objsubid IS NOT DISTINCT FROM blocked_locks.objsubid
                    AND blocking_locks.pid != blocked_locks.pid
                JOIN pg_catalog.pg_stat_activity blocking_activity ON blocking_activity.pid = blocking_locks.pid
                WHERE NOT blocked_locks.granted;
            """))

            locks = result.fetchall()
            if locks:
                logger.info(f"Found {len(locks)} locked transactions. Attempting to terminate blockers...")
                for lock in locks:
                    try:
                        logger.info(f"Terminating blocker PID: {lock.blocking_pid}")
                        conn.execute(text(f"SELECT pg_terminate_backend({lock.blocking_pid})"))
                    except Exception as e:
                        logger.warning(f"Error terminating blocker: {e}")
            else:
                logger.info("No transaction locks found.")

        logger.info("Transaction reset completed successfully.")
        return True
    except Exception as e:
        logger.error(f"Error resetting PostgreSQL transactions: {e}")
        return False

def setup_flask_app(database_url):
    """Initialize the Flask app with a minimal configuration"""
    logger.info("Setting up Flask application...")

    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize the database
    from app import db
    db.init_app(app)

    return app

def fix_database_schema(app):
    """Apply any necessary database schema fixes"""
    logger.info("Checking and fixing database schema...")

    with app.app_context():
        try:
            from app import db
            from sqlalchemy import inspect

            # Get database inspector
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()

            logger.info(f"Found tables: {', '.join(tables) if tables else 'No tables'}")

            # Check for critical missing tables
            critical_tables = ['users', 'site_settings', 'registration_requests']
            missing_tables = [table for table in critical_tables if table not in tables]

            if missing_tables:
                logger.warning(f"Critical tables are missing: {', '.join(missing_tables)}")
                logger.warning("Creating missing database tables using db.create_all()")
                try:
                    # Import all models to ensure they're registered with SQLAlchemy
                    from app.models import User, Property, PropertyCalendar, Room, Task, TaskAssignment
                    # Create tables
                    db.create_all()
                    logger.info("Successfully created all missing database tables")

                    # Initialize site settings if not already present
                    from app.models import SiteSettings
                    if SiteSettings.query.count() == 0:
                        logger.info("Creating default site settings...")
                        settings = [
                            SiteSettings(key='guest_reviews_enabled', value='True', description='Enable guest reviews', visible=True),
                            SiteSettings(key='cleaning_checklist_enabled', value='True', description='Enable cleaning checklists', visible=True),
                            SiteSettings(key='maintenance_requests_enabled', value='True', description='Enable maintenance requests', visible=True),
                            SiteSettings(key='require_cleaning_videos', value='False', description='Require videos for cleaning sessions', visible=True),
                        ]

                        for setting in settings:
                            db.session.add(setting)

                        db.session.commit()
                        logger.info(f"Created {len(settings)} default site settings.")
                except Exception as e:
                    logger.error(f"Error creating tables: {e}")
                    return False, missing_tables

            # Check if users table exists
            if 'users' in tables:
                logger.info("Users table found. Checking columns...")

                # Check column lengths
                try:
                    from sqlalchemy import text
                    with db.engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
                        # Check password_hash column length
                        result = conn.execute(text("""
                            SELECT column_name, character_maximum_length
                            FROM information_schema.columns
                            WHERE table_name = 'users' AND column_name = 'password_hash'
                        """))

                        column_info = result.fetchone()
                        if column_info and column_info.character_maximum_length < 256:
                            logger.info(f"Fixing password_hash column length (current: {column_info.character_maximum_length})")
                            conn.execute(text("ALTER TABLE users ALTER COLUMN password_hash TYPE VARCHAR(256)"))
                            logger.info("Column fixed.")
                except Exception as e:
                    logger.error(f"Error checking/fixing column lengths: {e}")
            else:
                logger.info("Users table not found. Tables may need to be created.")

            logger.info("Database schema check completed.")
            return True, missing_tables
        except Exception as e:
            logger.error(f"Error fixing database schema: {e}")
            return False, []

def main():
    """Main function that gets called when this script is run directly"""
    logger.info("Starting database initialization and fixes...")

    success, config = wait_for_postgres()
    if not success:
        logger.error("Could not connect to PostgreSQL. Exiting.")
        sys.exit(1)

    # Reset any hanging transactions
    reset_postgres_transactions(config['url'])

    try:
        # Add the parent directory to sys.path so we can import 'app'
        parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        sys.path.insert(0, parent_dir)

        # CRITICAL FIX: Set up Flask app first and create tables if needed
        app = setup_flask_app(config['url'])

        with app.app_context():
            # Check if critical tables are missing and create them
            from app import db
            from sqlalchemy import inspect

            inspector = inspect(db.engine)
            tables = inspector.get_table_names()

            critical_tables = ['users', 'site_settings', 'registration_requests']
            missing_tables = [table for table in critical_tables if table not in tables]

            if missing_tables:
                logger.warning(f"Critical tables are missing: {', '.join(missing_tables)}")
                logger.warning("Creating database tables using db.create_all()")

                # Import all models to ensure they're registered with SQLAlchemy
                from app.models import User, Property, PropertyCalendar, Room, Task, TaskAssignment
                # Make sure all models are imported before create_all
                try:
                    from app.models import SiteSettings, RegistrationRequest
                except ImportError:
                    logger.warning("Some models could not be imported, continuing anyway")

                # Create all tables
                try:
                    db.create_all()
                    logger.info("Successfully created all database tables")

                    # Initialize site settings if not already present
                    try:
                        from app.models import SiteSettings
                        if SiteSettings.query.count() == 0:
                            logger.info("Creating default site settings...")
                            settings = [
                                SiteSettings(key='guest_reviews_enabled', value='True', description='Enable guest reviews', visible=True),
                                SiteSettings(key='cleaning_checklist_enabled', value='True', description='Enable cleaning checklists', visible=True),
                                SiteSettings(key='maintenance_requests_enabled', value='True', description='Enable maintenance requests', visible=True),
                                SiteSettings(key='require_cleaning_videos', value='False', description='Require videos for cleaning sessions', visible=True),
                            ]

                            for setting in settings:
                                db.session.add(setting)

                            db.session.commit()
                            logger.info(f"Created {len(settings)} default site settings.")
                    except Exception as e:
                        logger.error(f"Error creating site settings: {e}")
                except Exception as e:
                    logger.error(f"Error creating tables with db.create_all(): {e}")

        try:
            # Use consolidated migrations first
            logger.info("Running consolidated migrations...")

            # Import and run consolidated user migrations
            try:
                from consolidated_user_migrations import run_consolidated_migrations as run_user_migrations
                logger.info("Running consolidated user migrations...")
                run_user_migrations()
            except Exception as e:
                logger.error(f"Error running consolidated user migrations: {e}")
                # Fall back to individual migrations in case of failure
                logger.info("Falling back to individual migrations...")

                try:
                    from model_fix import fix_user_model
                    logger.info("Running User model fix...")
                    fix_user_model()
                except Exception as e:
                    logger.error(f"Error running User model fix: {e}")

                try:
                    from create_users_table import create_users_table
                    logger.info("Running create_users_table script...")
                    create_users_table()
                except Exception as e:
                    logger.error(f"Error running create_users_table: {e}")

                try:
                    from create_admin import create_admin
                    logger.info("Creating/updating admin user from environment...")
                    create_admin()
                except Exception as e:
                    logger.error(f"Error creating admin user: {e}")

            # Import and run consolidated property migrations
            try:
                from consolidated_property_migrations import run_consolidated_property_migrations
                logger.info("Running consolidated property migrations...")
                run_consolidated_property_migrations()
            except Exception as e:
                logger.error(f"Error running consolidated property migrations: {e}")
                # Fall back to individual migrations in case of failure

                try:
                    from add_property_address_fields import add_property_address_fields
                    logger.info("Running add_property_address_fields script...")
                    add_property_address_fields()
                except Exception as e:
                    logger.error(f"Error running add_property_address_fields: {e}")

                try:
                    from add_property_details import add_property_details_fields
                    logger.info("Running add_property_details_fields script...")
                    add_property_details_fields()
                except Exception as e:
                    logger.error(f"Error running add_property_details_fields: {e}")

        except ImportError as e:
            logger.error(f"Could not import consolidated migrations: {e}")
            logger.warning("Running individual migrations instead...")

            # Run individual migrations
            try:
                from model_fix import fix_user_model
                logger.info("Running User model fix...")
                fix_user_model()
            except Exception as e:
                logger.error(f"Error running User model fix: {e}")

            try:
                from app_init_patch import patch_app_init
                logger.info("Applying app initialization patch...")
                patch_app_init()
            except Exception as e:
                logger.error(f"Error applying app init patch: {e}")

            try:
                from create_users_table import create_users_table
                logger.info("Running create_users_table script...")
                create_users_table()
            except Exception as e:
                logger.error(f"Error running create_users_table: {e}")

            try:
                from add_property_address_fields import add_property_address_fields
                logger.info("Running add_property_address_fields script...")
                add_property_address_fields()
            except Exception as e:
                logger.error(f"Error running add_property_address_fields: {e}")

            try:
                from add_property_details import add_property_details_fields
                logger.info("Running add_property_details_fields script...")
                add_property_details_fields()
            except Exception as e:
                logger.error(f"Error running add_property_details_fields: {e}")

        # Set up Flask app to use for more complex migrations
        app = setup_flask_app(config['url'])

        with app.app_context():
            # Fix database schema issues
            fix_database_schema(app)

            # Run any other necessary migrations
            try:
                logger.info("Checking for additional database fixes...")

                # Import and run additional fixes
                try:
                    from fix_fk_constraints import fix_foreign_keys
                    logger.info("Fixing foreign key constraints...")
                    fix_foreign_keys()
                except Exception as e:
                    logger.error(f"Error fixing foreign keys: {e}")

                try:
                    from fix_postgres_schema import fix_postgres_schema
                    logger.info("Fixing PostgreSQL schema issues...")
                    fix_postgres_schema()
                except Exception as e:
                    logger.error(f"Error fixing PostgreSQL schema: {e}")

                try:
                    from fix_task_template import fix_task_templates
                    logger.info("Fixing task templates...")
                    fix_task_templates()
                except Exception as e:
                    logger.error(f"Error fixing task templates: {e}")

                try:
                    from initialize_task_templates import initialize_templates
                    logger.info("Initializing task templates...")
                    initialize_templates()
                except Exception as e:
                    logger.error(f"Error initializing task templates: {e}")

                try:
                    from fix_site_settings import fix_site_settings
                    logger.info("Fixing site settings...")
                    fix_site_settings()
                except Exception as e:
                    logger.error(f"Error fixing site settings: {e}")
            except Exception as e:
                logger.error(f"Error running additional database fixes: {e}")

        logger.info("All database fixes completed. System is ready.")
    except Exception as e:
        logger.error(f"Unexpected error during database initialization: {e}")
        sys.exit(1)

if __name__ == "__main__":
    sys.exit(main())