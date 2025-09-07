#!/usr/bin/env python
"""
Fix for user search that works with any database schema
"""
import sys
import json
from pathlib import Path
import sqlite3
from sqlalchemy import text, inspect, MetaData

# Add the parent directory to sys.path
parent_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(parent_dir))

from app import create_app, db
from app.models import User, UserRoles

def direct_user_search(search_term):
    """Perform a direct SQL search that works with any schema"""
    print(f"Performing direct SQL search for '{search_term}'...")
    
    # First, detect which columns exist in the user table
    inspector = inspect(db.engine)
    columns = []
    try:
        columns = [col['name'] for col in inspector.get_columns('user')]
        print(f"Detected columns: {columns}")
    except Exception as e:
        print(f"Error detecting columns: {e}")
        # Fall back to minimal set
        columns = ['id', 'first_name', 'last_name', 'email']
    
    # Build a query based on existing columns
    dialect = db.engine.dialect.name
    select_columns = ['id', 'first_name', 'last_name', 'email']
    
    # Add other columns if they exist
    for col in ['username', 'authentik_id', 'signal_identity', 'is_active', 'is_admin']:
        if col in columns:
            select_columns.append(col)
    
    # Special handling for attributes which has different syntax by dialect
    attributes_condition = ""
    if 'attributes' in columns:
        select_columns.append('attributes')
        if dialect == 'postgresql':
            # PostgreSQL uses JSON operators
            attributes_condition = """
            OR CAST((attributes ->> 'intro') AS VARCHAR) ILIKE :search
            OR CAST((attributes ->> 'invited_by') AS VARCHAR) ILIKE :search
            """
        else:
            # SQLite doesn't have JSON operators but we can include the column
            pass
    
    # Build WHERE clause for basic fields
    where_conditions = []
    for field in ['username', 'first_name', 'last_name', 'email']:
        if field in columns:
            where_conditions.append(f"{field} LIKE :search")
    
    # Complete the query
    select_str = ", ".join(select_columns)
    where_str = " OR ".join(where_conditions)
    query = f"""
    SELECT {select_str} FROM "user" 
    WHERE {where_str} {attributes_condition}
    """
    
    # Execute the query
    try:
        result = db.session.execute(text(query), {'search': f'%{search_term}%'})
        rows = result.fetchall()
        print(f"Search found {len(rows)} users")
        
        # Convert the results to a list of dictionaries
        users = []
        for row in rows:
            user_dict = {}
            for i, col in enumerate(select_columns):
                if col == 'attributes' and row[i] and dialect != 'postgresql':
                    # Parse JSON from SQLite text column
                    try:
                        user_dict[col] = json.loads(row[i])
                    except:
                        user_dict[col] = row[i]
                else:
                    user_dict[col] = row[i]
            users.append(user_dict)
            
        # Print the results
        for user in users:
            print(f"  - {user.get('first_name', '')} {user.get('last_name', '')} ({user.get('email', '')})")
            if 'username' in user:
                print(f"    Username: {user['username']}")
            if 'authentik_id' in user:
                print(f"    Authentik ID: {user['authentik_id']}")
            if 'attributes' in user and user['attributes']:
                print(f"    Attributes: {user['attributes']}")
                
        return users
        
    except Exception as e:
        print(f"Error executing search query: {e}")
        return []

def update_postgresql_with_username():
    """Update PostgreSQL users with username from email if missing"""
    dialect = db.engine.dialect.name
    if dialect != 'postgresql':
        print("Not a PostgreSQL database, skipping")
        return
        
    print("Updating PostgreSQL users with username from email...")
    
    # Check if username column exists
    inspector = inspect(db.engine)
    try:
        columns = [col['name'] for col in inspector.get_columns('users')]
        if 'username' not in columns:
            print("Username column doesn't exist, skipping")
            return
    except Exception as e:
        print(f"Error checking columns: {e}")
        return
    
    # Get users with no username
    try:
        conn = db.engine.raw_connection()
        cursor = conn.cursor()
        cursor.execute("""
        UPDATE users 
        SET username = LOWER(SUBSTRING(email FROM 1 FOR POSITION('@' IN email) - 1))
        WHERE username IS NULL OR username = ''
        """)
        
        rows_affected = cursor.rowcount
        conn.commit()
        print(f"Updated {rows_affected} users with username from email")
        conn.close()
    except Exception as e:
        print(f"Error updating usernames: {e}")

def patch_search_query(search_term):
    """Generate the correct search query for the current database schema"""
    dialect = db.engine.dialect.name
    
    # For PostgreSQL, return the query to use for users table
    if dialect == 'postgresql':
        return f"""
        SELECT 
            id, username, email, first_name, last_name, is_active, is_admin,
            date_joined, last_login, attributes, authentik_id, signal_identity
        FROM users 
        WHERE username ILIKE '%{search_term}%'
           OR first_name ILIKE '%{search_term}%'
           OR last_name ILIKE '%{search_term}%'
           OR email ILIKE '%{search_term}%'
           OR CAST((attributes ->> 'intro') AS VARCHAR) ILIKE '%{search_term}%'
           OR CAST((attributes ->> 'invited_by') AS VARCHAR) ILIKE '%{search_term}%'
        ORDER BY username ASC
        """
    
    # For SQLite, return query for user table without problematic columns
    else:
        return f"""
        SELECT id, email, first_name, last_name 
        FROM user
        WHERE first_name LIKE '%{search_term}%'
           OR last_name LIKE '%{search_term}%'
           OR email LIKE '%{search_term}%'
        ORDER BY email ASC
        """

def test_search():
    search_terms = ["admin", "test", "example"]
    
    # Generate query based on schema
    for term in search_terms:
        print(f"\nDemonstrating search for '{term}':")
        print(f"SQL query that would work for this database:")
        query = patch_search_query(term)
        print(query)
        
        print("\nRunning actual search:")
        users = direct_user_search(term)
        print(f"Found {len(users)} users")

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        # If using PostgreSQL, update usernames from emails
        update_postgresql_with_username()
        
        # Test the direct search
        test_search() 