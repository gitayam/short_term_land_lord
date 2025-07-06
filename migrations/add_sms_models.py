#!/usr/bin/env python3
"""
Migration script to add SMS messaging models.
This script creates the message_threads and messages tables.
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
logger = logging.getLogger('sms_migration')

def create_app():
    """Create a minimal Flask app for database operations"""
    app = Flask(__name__)
    
    # Get database URL from environment or use default
    database_url = os.environ.get('DATABASE_URL', 'sqlite:///app.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize extensions
    from app import db
    db.init_app(app)
    
    return app, db

def add_sms_models():
    """Add SMS messaging models to the database"""
    app, db = create_app()
    
    with app.app_context():
        try:
            logger.info("Starting SMS models migration...")
            
            # Check if tables already exist
            inspector = db.inspect(db.engine)
            existing_tables = inspector.get_table_names()
            
            if 'message_threads' in existing_tables and 'messages' in existing_tables:
                logger.info("SMS tables already exist, skipping migration")
                return
            
            # Import models to ensure they're registered
            from app.models import MessageThread, Message
            
            # Create tables
            logger.info("Creating message_threads table...")
            MessageThread.__table__.create(db.engine, checkfirst=True)
            
            logger.info("Creating messages table...")
            Message.__table__.create(db.engine, checkfirst=True)
            
            logger.info("SMS models migration completed successfully!")
            
        except Exception as e:
            logger.error(f"Error during SMS models migration: {str(e)}")
            raise

def main():
    """Main migration function"""
    try:
        add_sms_models()
        print("✅ SMS models migration completed successfully!")
    except Exception as e:
        print(f"❌ SMS models migration failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 