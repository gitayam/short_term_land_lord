#!/usr/bin/env python
"""
Test script to verify user search functionality works with the new schema
"""
import sys
from pathlib import Path
import sqlalchemy as sa
from sqlalchemy import or_, text

# Add the parent directory to sys.path
parent_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(parent_dir))

from app import create_app, db
from app.models import User

def test_user_search():
    print("Testing user search functionality...")
    
    # Attempt a user search similar to the one in the error
    try:
        search_term = 'test'
        query = User.query.filter(
            or_(
                User.username.ilike(f'%{search_term}%'),
                User.first_name.ilike(f'%{search_term}%'),
                User.last_name.ilike(f'%{search_term}%'),
                User.email.ilike(f'%{search_term}%')
            )
        )
        
        # Try to execute the query
        users = query.all()
        print(f"Search successful! Found {len(users)} users matching '{search_term}'")
        for user in users:
            print(f"  - {user.get_full_name()} ({user.email})")
        
        # Now test with attributes if it exists
        if hasattr(User, 'attributes') and User.attributes is not None:
            try:
                # This is similar to the query in the error
                sql = text("""
                SELECT id, email FROM "user" 
                WHERE email ILIKE :search 
                   OR first_name ILIKE :search 
                   OR last_name ILIKE :search
                """)
                result = db.session.execute(sql, {'search': f'%{search_term}%'})
                rows = result.fetchall()
                print(f"Raw SQL search successful! Found {len(rows)} users")
            except Exception as e:
                print(f"Raw SQL search error: {e}")
                
    except Exception as e:
        print(f"Error during search: {e}")
        print("Let's try to identify what columns exist in the user/users table:")
        
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
                    result = conn.execute(text("PRAGMA table_info(user)"))
                    columns = result.fetchall()
                    if columns:
                        print(f"Table 'user' exists with columns: {[col[1] for col in columns]}")
                    else:
                        print("Table 'user' does not exist or has no columns")
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