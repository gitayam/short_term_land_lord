#!/usr/bin/env python3
"""
Database reset/creation script.
This script creates all database tables directly using SQLAlchemy's create_all method.
It's a fallback in case Flask-Migrate's migration-based approach fails.
"""

import os
import sys
from flask import Flask
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('db_reset')

def create_app():
    """Create a minimal Flask app for database operations"""
    app = Flask(__name__)
    
    # Get database URL from environment or use default
    database_url = os.environ.get('DATABASE_URL', 'postgresql://postgres:postgres@db/flask_app')
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize extensions
    from app import db
    db.init_app(app)
    
    return app, db

def reset_database():
    """Create all tables in the database"""
    logger.info("Creating database tables using SQLAlchemy's create_all...")
    
    try:
        # Create app and get db
        app, db = create_app()
        
        with app.app_context():
            # Import all models to ensure they're registered with SQLAlchemy
            from app.models import User, Property, Task, TaskAssignment, Room
            
            # Check if users table exists
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            if 'users' in tables and 'site_settings' in tables:
                logger.info("Critical tables already exist. Skipping table creation.")
                return True
            
            # Create all tables
            logger.info("Creating all database tables...")
            try:
                # Attempt direct creation with SQLAlchemy
                db.create_all()
                logger.info("Successfully created all database tables.")
                
                # Try to create an admin user if none exists
                try:
                    admin_count = db.session.execute(
                        db.text("SELECT COUNT(*) FROM users WHERE role = 'admin'")
                    ).scalar()
                    
                    if admin_count == 0:
                        # Get admin credentials from environment
                        admin_email = os.environ.get('ADMIN_EMAIL')
                        admin_password = os.environ.get('ADMIN_PASSWORD')
                        admin_first_name = os.environ.get('ADMIN_FIRST_NAME', 'System')
                        admin_last_name = os.environ.get('ADMIN_LAST_NAME', 'Administrator')
                        
                        if admin_email and admin_password:
                            logger.info(f"Creating admin user from environment: {admin_email}")
                            admin = User(
                                username=admin_email.split('@')[0],
                                email=admin_email,
                                first_name=admin_first_name,
                                last_name=admin_last_name,
                                role="admin",
                                is_admin=True
                            )
                            admin.set_password(admin_password)
                            db.session.add(admin)
                            db.session.commit()
                            logger.info(f"Admin user {admin_email} created successfully.")
                        else:
                            # Create default admin as fallback
                            logger.warning("No admin credentials in environment, creating default admin@example.com")
                            admin = User(
                                username="admin",
                                email="admin@example.com",
                                first_name="Admin",
                                last_name="User",
                                role="admin",
                                is_admin=True
                            )
                            admin.set_password('adminpass')
                            db.session.add(admin)
                            db.session.commit()
                            logger.info("Default admin user created successfully.")
                except Exception as e:
                    logger.warning(f"Could not create admin user: {e}")
                    db.session.rollback()
                
                return True
            except Exception as e:
                logger.error(f"Error creating tables: {e}")
                
                # Fallback to SQL script if create_all fails
                try:
                    logger.info("Attempting to create critical tables using SQL...")
                    
                    # Create critical tables using SQL
                    from sqlalchemy import text
                    
                    # Create users table if it doesn't exist
                    if 'users' not in tables:
                        logger.info("Creating users table...")
                        db.session.execute(text("""
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
                                authentik_id VARCHAR(36) UNIQUE,
                                signal_identity VARCHAR(36) UNIQUE,
                                attributes TEXT
                            )
                        """))
                    
                    # Create site_settings table if it doesn't exist
                    if 'site_settings' not in tables:
                        logger.info("Creating site_settings table...")
                        db.session.execute(text("""
                            CREATE TABLE IF NOT EXISTS site_settings (
                                key VARCHAR(64) PRIMARY KEY,
                                value TEXT,
                                description VARCHAR(255),
                                visible BOOLEAN DEFAULT TRUE,
                                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                            )
                        """))
                        
                        # Insert default site settings
                        logger.info("Adding default site settings...")
                        default_settings = [
                            ('site_name', 'Property Management System', 'System site name'),
                            ('support_email', 'support@example.com', 'Support email address'),
                            ('maintenance_phone', '555-123-4567', 'Maintenance phone number'),
                            ('enable_registration', 'true', 'Allow new user registration'),
                            ('require_approval', 'true', 'Require admin approval for new users'),
                            ('theme_primary_color', '#3f51b5', 'Primary theme color'),
                            ('theme_secondary_color', '#f50057', 'Secondary theme color'),
                            ('guest_reviews_enabled', 'true', 'Enable guest reviews feature')
                        ]
                        
                        for key, value, description in default_settings:
                            db.session.execute(text("""
                                INSERT INTO site_settings (key, value, description, visible)
                                VALUES (:key, :value, :description, TRUE)
                                ON CONFLICT (key) DO NOTHING
                            """), {'key': key, 'value': value, 'description': description})
                    
                    # Create registration_requests table if it doesn't exist
                    if 'registration_requests' not in tables:
                        logger.info("Creating registration_requests table...")
                        db.session.execute(text("""
                            CREATE TABLE IF NOT EXISTS registration_requests (
                                id SERIAL PRIMARY KEY,
                                first_name VARCHAR(64) NOT NULL,
                                last_name VARCHAR(64) NOT NULL,
                                email VARCHAR(120) NOT NULL,
                                phone VARCHAR(20),
                                role VARCHAR(20) NOT NULL,
                                password_hash VARCHAR(256) NOT NULL,
                                property_name VARCHAR(128),
                                property_address VARCHAR(256),
                                property_description TEXT,
                                message TEXT,
                                admin_notes TEXT,
                                status VARCHAR(20) DEFAULT 'pending',
                                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                reviewed_by INTEGER REFERENCES users(id)
                            )
                        """))
                    
                    # Create admin_actions table if it doesn't exist
                    if 'admin_actions' not in tables:
                        logger.info("Creating admin_actions table...")
                        db.session.execute(text("""
                            CREATE TABLE IF NOT EXISTS admin_actions (
                                id SERIAL PRIMARY KEY,
                                admin_id INTEGER NOT NULL REFERENCES users(id),
                                target_user_id INTEGER NOT NULL REFERENCES users(id),
                                action_type VARCHAR(50) NOT NULL,
                                action_details TEXT,
                                ip_address VARCHAR(45),
                                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                CONSTRAINT fk_admin_actions_admin FOREIGN KEY (admin_id) REFERENCES users(id),
                                CONSTRAINT fk_admin_actions_target FOREIGN KEY (target_user_id) REFERENCES users(id)
                            );
                            CREATE INDEX ix_admin_actions_admin_id ON admin_actions (admin_id);
                            CREATE INDEX ix_admin_actions_target_user_id ON admin_actions (target_user_id);
                            CREATE INDEX ix_admin_actions_created_at ON admin_actions (created_at);
                        """))
                    
                    db.session.commit()
                    logger.info("Successfully created critical tables using SQL.")
                    return True
                except Exception as sql_e:
                    logger.error(f"Error creating tables with SQL: {sql_e}")
                    db.session.rollback()
                    return False
    except Exception as e:
        logger.error(f"Unexpected error creating database tables: {e}")
        return False

if __name__ == "__main__":
    success = reset_database()
    sys.exit(0 if success else 1) 