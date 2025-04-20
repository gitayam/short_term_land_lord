#!/usr/bin/env python
"""
Simplified database fix script that ensures the 'users' table exists
and has all the necessary foreign key relationships.

This script is simplified since we now use a static table name approach
where the User model always uses 'users' as the table name.
"""

import os
import sys
import time
import psycopg2
from psycopg2 import sql
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_database():
    """Fix database tables and foreign keys to ensure everything uses 'users' table consistently."""
    database_url = os.environ.get('DATABASE_URL')
    
    if not database_url:
        logger.error("DATABASE_URL environment variable not set")
        return False
    
    # Handle postgres:// vs postgresql:// scheme difference
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    # Early return for SQLite - no fixes needed for SQLite
    if database_url.startswith('sqlite://'):
        logger.info("SQLite database detected. No fixes needed.")
        return True
    
    # Try to connect to the database - retry logic for container startup
    retry_count = 0
    max_retries = 10
    retry_delay = 2  # seconds
    
    while retry_count < max_retries:
        try:
            # Parse the URL to get connection parameters
            try:
                # Extract connection info from DATABASE_URL
                connection_string = database_url.replace('postgresql://', '')
                credentials_host = connection_string.split('@')
                
                if len(credentials_host) != 2:
                    logger.error(f"Invalid DATABASE_URL format: {database_url}")
                    return False
                
                credentials, host_part = credentials_host
                
                cred_parts = credentials.split(':')
                if len(cred_parts) != 2:
                    logger.error(f"Invalid credentials in DATABASE_URL")
                    return False
                    
                username, password = cred_parts
                
                host_parts = host_part.split('/')
                if len(host_parts) < 2:
                    logger.error(f"Invalid host format in DATABASE_URL")
                    return False
                    
                host_port = host_parts[0]
                dbname = host_parts[1].split('?')[0]  # Remove any query parameters
                
                if ':' in host_port:
                    host, port = host_port.split(':')
                    port = int(port)
                else:
                    host = host_port
                    port = 5432
            except Exception as e:
                logger.error(f"Error parsing DATABASE_URL: {e}")
                return False

            # Connect to the database
            logger.info(f"Connecting to PostgreSQL database at {host}...")
            conn = psycopg2.connect(
                dbname=dbname,
                user=username,
                password=password,
                host=host,
                port=port
            )
            conn.autocommit = False
            cursor = conn.cursor()
            
            # If we get here, connection is successful
            break
        except psycopg2.OperationalError as e:
            retry_count += 1
            if retry_count < max_retries:
                logger.warning(f"Failed to connect to database (attempt {retry_count}/{max_retries}): {e}")
                logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                logger.error(f"Failed to connect to database after {max_retries} attempts: {e}")
                return False
        except Exception as e:
            logger.error(f"Error connecting to database: {e}")
            return False

    try:
        # Check if 'user' table exists (old name)
        cursor.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'user')")
        user_table_exists = cursor.fetchone()[0]
        
        # Check if 'users' table exists (new name)
        cursor.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'users')")
        users_table_exists = cursor.fetchone()[0]
        
        if user_table_exists and not users_table_exists:
            # Rename the table from 'user' to 'users'
            logger.info("Renaming 'user' table to 'users'...")
            cursor.execute('ALTER TABLE "user" RENAME TO users')
            logger.info("Table renamed successfully.")
        elif user_table_exists and users_table_exists:
            logger.warning("Both 'user' and 'users' tables exist. This is an inconsistent state.")
            
            # Check if they have the same structure
            cursor.execute("SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'user'")
            user_columns = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'users'")
            users_columns = cursor.fetchone()[0]
            
            if user_columns == users_columns:
                logger.info("Tables appear to have the same structure. You may want to drop the 'user' table manually.")
            else:
                logger.warning("Tables have different structures. Manual intervention required.")
        elif not user_table_exists and not users_table_exists:
            logger.info("Neither 'user' nor 'users' table exists. Tables will be created by migrations.")
        
        # Commit changes
        conn.commit()
        logger.info("Database fix attempts completed.")
        return True
    except Exception as e:
        logger.error(f"Error fixing database: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    fix_database() 