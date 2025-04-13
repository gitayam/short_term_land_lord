#!/usr/bin/env python
"""
Database reset utility script.
Creates all tables if they don't exist.
"""

import os
import sys
import json
from flask import Flask
from sqlalchemy import text

# Create a minimal Flask app
app = Flask(__name__)

# Configure the app from environment variables
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Import and initialize the database
from app import db, create_app

def reset_db():
    """Create database tables if they don't exist"""
    try:
        # Check if we're using PostgreSQL and ensure JSON operators are created
        if 'postgresql' in app.config['SQLALCHEMY_DATABASE_URI']:
            with db.engine.connect() as conn:
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS hstore"))
                conn.commit()

        # Create all tables
        print("Creating database tables...")
        db.create_all()
        print("Database tables created successfully.")
        
        return True
    except Exception as e:
        print(f"Error creating database tables: {e}", file=sys.stderr)
        return False

if __name__ == '__main__':
    # Initialize the app context
    app = create_app()
    with app.app_context():
        success = reset_db()
        sys.exit(0 if success else 1) 