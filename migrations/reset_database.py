#!/usr/bin/env python
"""
Database reset script that drops all tables and recreates them.
This is useful when migrations fail and you need a clean start.
"""

import os
import sys
import time
from flask import Flask
from sqlalchemy import text

def reset_database():
    """Drop all tables and recreate them."""
    # Create a minimal Flask app
    app = Flask(__name__)
    
    # Configure the app
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize the database
    from app import db
    db.init_app(app)
    
    with app.app_context():
        try:
            # Get all table names
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            
            print(f"Found {len(tables)} tables in database")
            print(f"Tables: {', '.join(tables)}")
            
            # Drop all tables
            print("Dropping all tables...")
            db.drop_all()
            print("All tables dropped successfully")
            
            # Create all tables
            print("Creating all tables with consistent schema...")
            db.create_all()
            print("All tables created successfully")
            
            # Initialize site settings and admin user
            print("Initializing site settings and admin user...")
            from app.models import migrate_site_settings, create_admin_user_from_env
            migrate_site_settings()
            create_admin_user_from_env()
            print("Site settings and admin user initialized successfully")
            
            return True
        except Exception as e:
            print(f"Error resetting database: {e}")
            return False

if __name__ == "__main__":
    reset_database() 