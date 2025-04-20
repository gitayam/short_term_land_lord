from flask import Flask
from app import db, create_app
from app.models import SiteSettings
from sqlalchemy import inspect

def main():
    """Initialize site_settings table and add default values"""
    app = create_app()
    with app.app_context():
        # Check if site_settings table exists
        try:
            # Create site_settings table if it doesn't exist
            inspector = inspect(db.engine)
            if not inspector.has_table('site_settings'):
                db.create_all(tables=[SiteSettings.__table__])
                print("Created site_settings table")
            
            # Initialize default settings
            if not SiteSettings.query.get('guest_reviews_enabled'):
                SiteSettings.set_setting('guest_reviews_enabled', 'true', 'Enable guest reviews feature', True)
                print("Added guest_reviews_enabled setting")
            
            # Set placeholder for OpenAI API key
            if not SiteSettings.query.get('openai_api_key'):
                SiteSettings.set_setting('openai_api_key', '', 'OpenAI API Key for AI functionality', False)
                print("Added openai_api_key setting")
            
            print("Site settings initialization completed successfully")
        except Exception as e:
            print(f"Error initializing site settings: {str(e)}")
            
if __name__ == '__main__':
    main() 