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
                logger.warning("Database tables need to be created. You should run 'flask db upgrade' or setup the database")
                logger.warning("The application may not function correctly until tables are created")
            
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
    """Main function to coordinate startup sequence"""
    logger.info("Starting database preparation sequence...")
    
    try:
        # Wait for PostgreSQL to be available
        postgres_ready, config = wait_for_postgres()
        if not postgres_ready:
            logger.error("PostgreSQL not available. Exiting.")
            sys.exit(1)
        
        # Reset any problematic transactions
        reset_result = reset_postgres_transactions(config['url'])
        if not reset_result:
            logger.warning("Transaction reset failed. Will continue anyway...")
        
        # Set up minimal Flask app for database operations
        app = setup_flask_app(config['url'])
        
        # Fix database schema if needed
        schema_result, missing_tables = fix_database_schema(app)
        if not schema_result:
            logger.warning("Schema fixes failed. Will continue anyway...")
        
        if missing_tables:
            logger.warning("Database is missing critical tables!")
            # We continue because this will be handled by migrations in run_db_fixes.sh
        
        logger.info("Database preparation completed successfully!")
        logger.info("Starting main application...")
        
        # In Docker, we'll exit and let the entrypoint script run the actual application
        # For local testing, you might want to run the app directly
        return 0
    except Exception as e:
        logger.error(f"Unexpected error during database preparation: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 