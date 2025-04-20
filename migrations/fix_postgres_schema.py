#!/usr/bin/env python
"""
PostgreSQL Schema Fix Utility.
This script fixes JSON columns by converting them to TEXT type for better compatibility.
"""

import os
import sys
from flask import Flask
from sqlalchemy import text, inspect

# Create a minimal Flask app
app = Flask(__name__)

# Configure the app from environment variables
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Import and initialize the database
from app import db, create_app

def fix_postgres_schema():
    """Fix PostgreSQL JSON columns by converting them to TEXT"""
    try:
        # Only run this for PostgreSQL databases
        if 'postgresql' not in app.config['SQLALCHEMY_DATABASE_URI']:
            print("Not using PostgreSQL. No schema fixes needed.")
            return True
            
        print("Checking PostgreSQL schema for JSON compatibility issues...")
        
        # Get database inspector
        inspector = inspect(db.engine)
        
        # Check if users table exists and has attributes column
        if 'users' in inspector.get_table_names():
            columns = {col['name']: col for col in inspector.get_columns('users')}
            
            # Check if attributes column exists and needs conversion
            if 'attributes' in columns:
                print("Converting users.attributes column from JSON to TEXT...")
                with db.engine.connect() as conn:
                    # Alter the column type to TEXT
                    conn.execute(text("ALTER TABLE users ALTER COLUMN attributes TYPE TEXT USING attributes::TEXT"))
                    conn.commit()
                print("Successfully converted users.attributes to TEXT.")
        
        # Add checks for other JSON columns here if needed
        
        return True
    except Exception as e:
        print(f"Error fixing PostgreSQL schema: {e}", file=sys.stderr)
        return False

if __name__ == '__main__':
    # Initialize the app context
    app = create_app()
    with app.app_context():
        success = fix_postgres_schema()
        sys.exit(0 if success else 1) 