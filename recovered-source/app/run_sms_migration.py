#!/usr/bin/env python3
"""
Simple script to run SMS migration using the existing app structure.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def run_migration():
    """Run the SMS migration"""
    try:
        from app import create_app, db
        from app.models import MessageThread, Message
        
        # Create app with default config
        app = create_app()
        
        with app.app_context():
            print("Starting SMS models migration...")
            
            # Check if tables already exist
            inspector = db.inspect(db.engine)
            existing_tables = inspector.get_table_names()
            
            if 'message_threads' in existing_tables and 'messages' in existing_tables:
                print("✅ SMS tables already exist, skipping migration")
                return
            
            # Create tables
            print("Creating message_threads table...")
            MessageThread.__table__.create(db.engine, checkfirst=True)
            
            print("Creating messages table...")
            Message.__table__.create(db.engine, checkfirst=True)
            
            print("✅ SMS models migration completed successfully!")
            
    except Exception as e:
        print(f"❌ SMS models migration failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    run_migration() 