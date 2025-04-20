#!/usr/bin/env python3
"""
Simplified database bootstrapping script for first-run initialization.
This script creates the minimum required tables directly using SQL
without requiring complex model imports.
"""

import os
import sys
import time
import datetime
from sqlalchemy import create_engine, inspect, text

def bootstrap_database():
    """Create minimal tables required for application startup"""
    # Set up database URL
    database_url = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@db/flask_app")
    print(f"Using database URL: {database_url}")

    # Check database connection
    try:
        engine = create_engine(database_url)
        with engine.connect() as conn:
            print("Database connection successful")
            
            # Check if tables exist
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            print(f"Existing tables: {tables}")
            
            if "users" not in tables:
                print("Creating users table directly with SQL...")
                # Create users table with ALL required columns
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY,
                        username VARCHAR(64) UNIQUE,
                        first_name VARCHAR(64),
                        last_name VARCHAR(64),
                        email VARCHAR(120) UNIQUE,
                        phone VARCHAR(20),
                        password_hash VARCHAR(256),
                        role VARCHAR(20),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        is_active BOOLEAN DEFAULT TRUE,
                        is_admin BOOLEAN DEFAULT FALSE,
                        last_login TIMESTAMP,
                        authentik_id VARCHAR(64),
                        signal_identity VARCHAR(64),
                        attributes JSONB
                    )
                """))
                print("Users table created successfully")
            else:
                print("Users table already exists, checking for missing columns...")
                # Check for and add any missing columns
                try:
                    user_columns = inspector.get_columns('users')
                    column_names = [col['name'] for col in user_columns]
                    
                    if 'authentik_id' not in column_names:
                        print("Adding authentik_id column to users table")
                        conn.execute(text("ALTER TABLE users ADD COLUMN authentik_id VARCHAR(64)"))
                    
                    if 'signal_identity' not in column_names:
                        print("Adding signal_identity column to users table")
                        conn.execute(text("ALTER TABLE users ADD COLUMN signal_identity VARCHAR(64)"))
                    
                    if 'attributes' not in column_names:
                        print("Adding attributes column to users table")
                        conn.execute(text("ALTER TABLE users ADD COLUMN attributes JSONB"))
                    
                    print("User table columns updated successfully")
                except Exception as e:
                    print(f"Error checking or adding columns: {e}")
            
            if "site_settings" not in tables:
                print("Creating site_settings table directly with SQL...")
                # Create site_settings table
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS site_settings (
                        key VARCHAR(64) PRIMARY KEY,
                        value TEXT,
                        description VARCHAR(255),
                        visible BOOLEAN DEFAULT TRUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                
                # Add basic site settings
                conn.execute(text("""
                    INSERT INTO site_settings (key, value, description, visible)
                    VALUES 
                        ('app_name', 'Property Management', 'Application Name', TRUE),
                        ('guest_reviews_enabled', 'True', 'Enable guest reviews', TRUE),
                        ('cleaning_checklist_enabled', 'True', 'Enable cleaning checklists', TRUE),
                        ('maintenance_requests_enabled', 'True', 'Enable maintenance requests', TRUE)
                    ON CONFLICT (key) DO NOTHING
                """))
                
                print("Site settings table created and populated successfully")
            
            # Check for any existing transactions (and commit them)
            try:
                conn.execute(text("COMMIT"))
                print("Committed any pending transactions")
            except:
                pass
                
            return True
    except Exception as e:
        print(f"Database error: {e}")
        return False

if __name__ == "__main__":
    print("Running database bootstrap script...")
    success = bootstrap_database()
    if success:
        print("Database initialization complete")
        sys.exit(0)
    else:
        print("Database initialization failed")
        sys.exit(1) 