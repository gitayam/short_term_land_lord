#!/usr/bin/env python
import os
import sys
from pathlib import Path

# Add the parent directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import create_app, db
from app.models import SiteSettings

def init_database():
    """Initialize the database by creating all tables"""
    print("Creating database tables...")
    db.create_all()
    
    # Initialize site settings if not already present
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
    
    print("Database initialization complete!")

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        init_database() 