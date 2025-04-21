#!/usr/bin/env python
import os
import sys
from pathlib import Path

# Add the parent directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

def init_database():
    """Initialize the database by creating all tables"""
    print("Creating database tables...")
    try:
        from app import create_app, db

        # Create app context
        print("Creating app context...")
        app = create_app()

        with app.app_context():
            print("Starting db.create_all()...")
            # First, import all models to ensure they're registered
            try:
                print("Importing models...")
                from app.models import SiteSettings, User, Property, Room, Task, TaskAssignment, PropertyCalendar
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
                from app.models import SiteSettings
                if SiteSettings.query.count() == 0:
                    print("Creating default site settings...")
                    settings = [
                        SiteSettings(key='guest_reviews_enabled', value='True', description='Enable guest reviews', visible=True),
                        SiteSettings(key='cleaning_checklist_enabled', value='True', description='Enable cleaning checklists', visible=True),
                        SiteSettings(key='maintenance_requests_enabled', value='True', description='Enable maintenance requests', visible=True),
                        SiteSettings(key='require_cleaning_videos', value='False', description='Require videos for cleaning sessions', visible=True),
                    ]

                    for setting in settings:
                        db.session.add(setting)

                    db.session.commit()
                    print(f"Created {len(settings)} default site settings.")
                else:
                    print("Site settings already exist.")
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