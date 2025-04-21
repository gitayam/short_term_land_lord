#!/usr/bin/env python3
"""Initialize database with required tables and initial data."""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add the parent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load environment variables from .env file
env_path = Path(os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))) / '.env'
load_dotenv(dotenv_path=env_path)

from app import create_app, db
from app.models import SiteSetting, User, Property, Room, Task, TaskAssignment, PropertyCalendar

def init_site_settings():
    """Initialize site settings with default values"""
    from app.models import SiteSetting
    if SiteSetting.query.count() == 0:
        # Create default settings
        settings = [
            SiteSetting(key='guest_reviews_enabled', value='True', description='Enable guest reviews', visible=True),
            SiteSetting(key='cleaning_checklist_enabled', value='True', description='Enable cleaning checklists', visible=True),
            SiteSetting(key='maintenance_requests_enabled', value='True', description='Enable maintenance requests', visible=True),
            SiteSetting(key='require_cleaning_videos', value='False', description='Require videos for cleaning sessions', visible=True),
        ]
        
        db.session.add_all(settings)
        db.session.commit()

def init_database():
    """Initialize the database by creating all tables"""
    print("Creating database tables...")
    try:
        # Create app context
        print("Creating app context...")
        app = create_app()
        
        with app.app_context():
            print("Starting db.create_all()...")
            # First, import all models to ensure they're registered
            try:
                print("Importing models...")
                from app.models import SiteSetting, User, Property, Room, Task, TaskAssignment, PropertyCalendar
                print("Models imported successfully")
            except ImportError as e:
                print(f"Warning: Error importing models: {e}")
                print("Continuing with available models")
            
            # Create all tables
            try:
                db.create_all()
                print("Created all tables successfully")
            except Exception as e:
                print(f"Error during db.create_all(): {e}")
                return False
            
            # Initialize site settings if not already present
            try:
                init_site_settings()
            except Exception as e:
                print(f"Error setting up site settings: {e}")
                db.session.rollback()
                
            print("Database initialization complete!")
            return True
    except Exception as e:
        print(f"Error during database initialization: {e}")
        return False

if __name__ == "__main__":
    print("Running init_db.py directly...")
    success = init_database()
    sys.exit(0 if success else 1) 