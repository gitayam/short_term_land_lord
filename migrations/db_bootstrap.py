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
    try:
        print("Running simplified database bootstrap script...")
        print(f"Using database URL: {os.getenv('DATABASE_URL')}")
        
        # Create engine and connect
        engine = create_engine(os.getenv('DATABASE_URL'))
        print("Database connection successful")
        
        # Check existing tables
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"Existing tables: {tables}")
        
        # Create tables if they don't exist
        with engine.connect() as conn:
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
                        is_suspended BOOLEAN DEFAULT FALSE,
                        last_login TIMESTAMP,
                        authentik_id VARCHAR(64),
                        signal_identity VARCHAR(64),
                        attributes JSONB,
                        profile_image VARCHAR(255),
                        timezone VARCHAR(50) DEFAULT 'UTC',
                        language VARCHAR(10) DEFAULT 'en',
                        theme_preference VARCHAR(20) DEFAULT 'light',
                        default_dashboard_view VARCHAR(20) DEFAULT 'tasks',
                        default_calendar_view VARCHAR(20) DEFAULT 'month',
                        default_task_sort VARCHAR(20) DEFAULT 'due_date',
                        email_notifications BOOLEAN DEFAULT TRUE,
                        sms_notifications BOOLEAN DEFAULT FALSE,
                        in_app_notifications BOOLEAN DEFAULT TRUE,
                        notification_frequency VARCHAR(20) DEFAULT 'immediate',
                        two_factor_enabled BOOLEAN DEFAULT FALSE,
                        two_factor_method VARCHAR(20),
                        last_password_change TIMESTAMP,
                        failed_login_attempts INTEGER DEFAULT 0,
                        locked_until TIMESTAMP,
                        last_failed_login TIMESTAMP,
                        google_calendar_connected BOOLEAN DEFAULT FALSE,
                        google_calendar_token TEXT,
                        twilio_phone_verified BOOLEAN DEFAULT FALSE,
                        slack_workspace_id VARCHAR(100),
                        invitation_code_id INTEGER,
                        guest_preferences TEXT,
                        last_check_in TIMESTAMP,
                        guest_rating FLOAT,
                        guest_notes TEXT,
                        marketing_emails_consent BOOLEAN DEFAULT FALSE,
                        booking_reminders_consent BOOLEAN DEFAULT TRUE,
                        email_verified BOOLEAN DEFAULT FALSE,
                        email_verification_token VARCHAR(64),
                        email_verification_sent_at TIMESTAMP
                    )
                """))
                print("Users table created successfully")
            else:
                print("Users table already exists, checking for missing columns...")
                # Check for and add any missing columns
                try:
                    user_columns = inspector.get_columns('users')
                    column_names = [col['name'] for col in user_columns]
                    
                    # List of all required columns and their types
                    required_columns = [
                        ('profile_image', 'VARCHAR(255)'),
                        ('timezone', 'VARCHAR(50) DEFAULT \'UTC\''),
                        ('language', 'VARCHAR(10) DEFAULT \'en\''),
                        ('theme_preference', 'VARCHAR(20) DEFAULT \'light\''),
                        ('default_dashboard_view', 'VARCHAR(20) DEFAULT \'tasks\''),
                        ('default_calendar_view', 'VARCHAR(20) DEFAULT \'month\''),
                        ('default_task_sort', 'VARCHAR(20) DEFAULT \'due_date\''),
                        ('email_notifications', 'BOOLEAN DEFAULT TRUE'),
                        ('sms_notifications', 'BOOLEAN DEFAULT FALSE'),
                        ('in_app_notifications', 'BOOLEAN DEFAULT TRUE'),
                        ('notification_frequency', 'VARCHAR(20) DEFAULT \'immediate\''),
                        ('two_factor_enabled', 'BOOLEAN DEFAULT FALSE'),
                        ('two_factor_method', 'VARCHAR(20)'),
                        ('last_password_change', 'TIMESTAMP'),
                        ('failed_login_attempts', 'INTEGER DEFAULT 0'),
                        ('locked_until', 'TIMESTAMP'),
                        ('last_failed_login', 'TIMESTAMP'),
                        ('google_calendar_connected', 'BOOLEAN DEFAULT FALSE'),
                        ('google_calendar_token', 'TEXT'),
                        ('twilio_phone_verified', 'BOOLEAN DEFAULT FALSE'),
                        ('slack_workspace_id', 'VARCHAR(100)'),
                        ('authentik_id', 'VARCHAR(64)'),
                        ('signal_identity', 'VARCHAR(64)'),
                        ('attributes', 'JSONB'),
                        ('invitation_code_id', 'INTEGER'),
                        ('guest_preferences', 'TEXT'),
                        ('last_check_in', 'TIMESTAMP'),
                        ('guest_rating', 'FLOAT'),
                        ('guest_notes', 'TEXT'),
                        ('marketing_emails_consent', 'BOOLEAN DEFAULT FALSE'),
                        ('booking_reminders_consent', 'BOOLEAN DEFAULT TRUE'),
                        ('email_verified', 'BOOLEAN DEFAULT FALSE'),
                        ('email_verification_token', 'VARCHAR(64)'),
                        ('email_verification_sent_at', 'TIMESTAMP')
                    ]
                    
                    for column_name, column_type in required_columns:
                        if column_name not in column_names:
                            print(f"Adding {column_name} column to users table")
                            conn.execute(text(f"ALTER TABLE users ADD COLUMN {column_name} {column_type}"))
                    
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
                        category VARCHAR(32),
                        config_type VARCHAR(16),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_by_id INTEGER
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