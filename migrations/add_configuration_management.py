#!/usr/bin/env python3
"""
Migration to add configuration management support
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask
from app import create_app, db
from app.models import SiteSetting, ConfigurationAudit
from sqlalchemy import inspect, text
from datetime import datetime

def run_migration():
    """Add configuration management fields to database"""
    
    app = create_app()
    
    with app.app_context():
        try:
            # Get database inspector
            inspector = inspect(db.engine)
            
            # Check if configuration_audit table exists
            if 'configuration_audit' not in inspector.get_table_names():
                print("Creating configuration_audit table...")
                
                # Create the ConfigurationAudit table
                db.create_all()
                print("✓ Created configuration_audit table")
            else:
                print("configuration_audit table already exists")
            
            # Check if new columns exist in site_settings table
            site_settings_columns = [col['name'] for col in inspector.get_columns('site_settings')]
            
            # Add missing columns to site_settings
            with db.engine.connect() as conn:
                if 'category' not in site_settings_columns:
                    print("Adding category column to site_settings...")
                    conn.execute(text("""
                        ALTER TABLE site_settings 
                        ADD COLUMN category VARCHAR(32)
                    """))
                    conn.commit()
                    print("✓ Added category column")
                
                if 'config_type' not in site_settings_columns:
                    print("Adding config_type column to site_settings...")
                    conn.execute(text("""
                        ALTER TABLE site_settings 
                        ADD COLUMN config_type VARCHAR(16)
                    """))
                    conn.commit()
                    print("✓ Added config_type column")
                
                if 'updated_by_id' not in site_settings_columns:
                    print("Adding updated_by_id column to site_settings...")
                    conn.execute(text("""
                        ALTER TABLE site_settings 
                        ADD COLUMN updated_by_id INTEGER REFERENCES users(id)
                    """))
                    conn.commit()
                    print("✓ Added updated_by_id column")
            
            # Update existing settings with categories
            print("Updating existing settings with categories...")
            
            # Map existing settings to categories
            setting_categories = {
                'openai_api_key': 'integration',
                'guest_reviews_enabled': 'features'
            }
            
            for key, category in setting_categories.items():
                setting = db.session.get(SiteSetting, key)
                if setting:
                    setting.category = category
                    print(f"  - Updated {key} category to {category}")
            
            db.session.commit()
            
            print("\n✅ Migration completed successfully!")
            print("\nConfiguration management support has been added.")
            print("You can now access the configuration management interface at /admin/configuration")
            
        except Exception as e:
            print(f"\n❌ Migration failed: {e}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    run_migration()