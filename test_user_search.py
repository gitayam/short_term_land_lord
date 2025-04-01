#!/usr/bin/env python
"""
Test script to verify user search functionality works with the new schema
"""
import sys
import os
import sqlite3
from pathlib import Path
import sqlalchemy as sa
from sqlalchemy import or_, text, inspect, MetaData

# Add the parent directory to sys.path
parent_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(parent_dir))

from app import create_app, db
from app.models import User

def test_user_search():
    print("Testing user search functionality...")
    
    # Force SQLAlchemy to reflect the current table structure
    print("Reflecting database structure...")
    inspector = inspect(db.engine)
    columns = []
    try:
        columns = inspector.get_columns('user')
        print(f"Reflected columns: {[col['name'] for col in columns]}")
    except Exception as e:
        print(f"Error reflecting columns: {e}")
    
    # Attempt a user search similar to the one in the error
    try:
        # First try direct SQL to avoid SQLAlchemy cache issues
        search_term = 'test'
        print(f"Testing direct SQL search for '{search_term}'...")
        
        try:
            # Use the raw SQL directly
            sql = text("""
            SELECT id, email FROM "user" 
            WHERE email LIKE :search 
               OR first_name LIKE :search 
               OR last_name LIKE :search
            """)
            result = db.session.execute(sql, {'search': f'%{search_term}%'})
            rows = result.fetchall()
            print(f"Direct SQL search successful! Found {len(rows)} users")
            for row in rows:
                print(f"  - User ID: {row[0]}, Email: {row[1]}")
        except Exception as e:
            print(f"Direct SQL search error: {e}")
        
        # Now try with SQLAlchemy ORM
        print(f"Testing SQLAlchemy ORM search for '{search_term}'...")
        try:
            query = User.query.filter(
                or_(
                    User.first_name.ilike(f'%{search_term}%'),
                    User.last_name.ilike(f'%{search_term}%'),
                    User.email.ilike(f'%{search_term}%')
                )
            )
            
            # Try to execute the query without username
            users = query.all()
            print(f"ORM search successful! Found {len(users)} users matching '{search_term}'")
            for user in users:
                print(f"  - {user.get_full_name()} ({user.email})")
        except Exception as e:
            print(f"ORM search error: {e}")
            
        # Only try username if it's reflected in the database
        if any(col['name'] == 'username' for col in columns):
            print(f"Testing search with username for '{search_term}'...")
            try:
                query = User.query.filter(
                    or_(
                        User.username.ilike(f'%{search_term}%'),
                        User.first_name.ilike(f'%{search_term}%'),
                        User.last_name.ilike(f'%{search_term}%'),
                        User.email.ilike(f'%{search_term}%')
                    )
                )
                users = query.all()
                print(f"Search with username successful! Found {len(users)} users")
            except Exception as e:
                print(f"Search with username error: {e}")
        
        # Test the advanced search like in the error message
        if any(col['name'] == 'attributes' for col in columns):
            print("Testing advanced search with attributes...")
            try:
                # This is for PostgreSQL and only works there
                sql = """
                SELECT id, email FROM "user" 
                WHERE email ILIKE :search 
                   OR first_name ILIKE :search 
                   OR last_name ILIKE :search
                """
                
                # Only add the attributes part if we're using PostgreSQL
                if db.engine.dialect.name == 'postgresql':
                    sql += """
                   OR CAST((attributes ->> 'intro') AS VARCHAR) ILIKE :search
                   OR CAST((attributes ->> 'invited_by') AS VARCHAR) ILIKE :search
                    """
                
                result = db.session.execute(text(sql), {'search': f'%{search_term}%'})
                rows = result.fetchall()
                print(f"Advanced search successful! Found {len(rows)} users")
            except Exception as e:
                print(f"Advanced search error: {e}")
                
    except Exception as e:
        print(f"Error during search: {e}")
    
    # Check what columns actually exist in the database
    print("Let's look at what columns exist in the database:")
    try:
        # Check connection and get database dialect
        dialect = db.engine.dialect.name
        print(f"Database dialect: {dialect}")
        
        # Get table information
        conn = db.engine.connect()
        if dialect == 'postgresql':
            # For PostgreSQL, check both user and users tables
            tables_to_check = ['user', 'users']
            for table in tables_to_check:
                try:
                    result = conn.execute(text(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table}'"))
                    columns = result.fetchall()
                    if columns:
                        print(f"Table '{table}' exists with columns: {[col[0] for col in columns]}")
                    else:
                        print(f"Table '{table}' does not exist or has no columns")
                except Exception as e:
                    print(f"Error checking table '{table}': {e}")
        else:
            # For SQLite
            try:
                # Check directly with SQLite
                db_path = 'app.db'
                sqlite_conn = sqlite3.connect(db_path)
                sqlite_cursor = sqlite_conn.cursor()
                sqlite_cursor.execute("PRAGMA table_info(user)")
                columns = sqlite_cursor.fetchall()
                print(f"SQLite PRAGMA shows 'user' table with columns: {[col[1] for col in columns]}")
                sqlite_conn.close()
                
                # Also check with SQLAlchemy
                result = conn.execute(text("PRAGMA table_info(user)"))
                columns = result.fetchall()
                if columns:
                    print(f"SQLAlchemy reports 'user' table with columns: {[col[1] for col in columns]}")
                else:
                    print("SQLAlchemy reports 'user' table does not exist or has no columns")
            except Exception as e:
                print(f"Error checking table 'user': {e}")
        
        conn.close()
    except Exception as e:
        print(f"Error checking database schema: {e}")
    
    print("Test completed!")

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        test_user_search() 