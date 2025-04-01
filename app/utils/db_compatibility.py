"""
Database compatibility utilities

This module provides functions to work with both SQLite and PostgreSQL databases,
handling schema differences transparently.
"""
import json
from sqlalchemy import text, inspect

from app import db

def search_users(search_term):
    """
    Search for users with a search term that works with both database schemas.
    Returns a list of dictionaries with user data.
    """
    # Detect which dialect we're using
    dialect = db.engine.dialect.name
    
    # Get the appropriate query for the dialect
    if dialect == 'postgresql':
        # PostgreSQL query - for the 'users' table with JSON attributes
        query = text("""
        SELECT 
            id, username, email, first_name, last_name, is_active, is_admin,
            date_joined, last_login, attributes, authentik_id, signal_identity
        FROM users 
        WHERE username ILIKE :search
           OR first_name ILIKE :search
           OR last_name ILIKE :search
           OR email ILIKE :search
           OR CAST((attributes ->> 'intro') AS VARCHAR) ILIKE :search
           OR CAST((attributes ->> 'invited_by') AS VARCHAR) ILIKE :search
        ORDER BY username ASC
        """)
    else:
        # SQLite query - for the 'user' table, only using columns that exist
        inspector = inspect(db.engine)
        try:
            columns = [col['name'] for col in inspector.get_columns('user')]
        except:
            # Fallback to minimal set
            columns = ['id', 'first_name', 'last_name', 'email']
        
        # Start with basic columns that should always exist
        select_columns = ['id', 'first_name', 'last_name', 'email']
        where_conditions = []
        
        # These are the basic search fields
        basic_fields = ['first_name', 'last_name', 'email']
        for field in basic_fields:
            if field in columns:
                where_conditions.append(f"{field} LIKE :search")
        
        # Add username if it exists
        if 'username' in columns:
            select_columns.append('username')
            where_conditions.append("username LIKE :search")
            
        # Add other optional columns if they exist
        optional_columns = ['authentik_id', 'signal_identity', 'is_active', 'is_admin', 'date_joined', 'last_login']
        for col in optional_columns:
            if col in columns:
                select_columns.append(col)
        
        # Add attributes if it exists
        if 'attributes' in columns:
            select_columns.append('attributes')
            
        # Build the query
        select_str = ", ".join(select_columns)
        where_str = " OR ".join(where_conditions)
        query_str = f"""
        SELECT {select_str}
        FROM user
        WHERE {where_str}
        ORDER BY email ASC
        """
        query = text(query_str)
    
    # Execute the query
    result = db.session.execute(query, {'search': f'%{search_term}%'})
    rows = result.fetchall()
    
    # Convert to dictionaries
    users = []
    for row in rows:
        user_dict = dict(row._mapping)
        
        # For SQLite, handle JSON attributes
        if dialect != 'postgresql' and 'attributes' in user_dict and user_dict['attributes']:
            try:
                user_dict['attributes'] = json.loads(user_dict['attributes'])
            except:
                pass
                
        users.append(user_dict)
    
    return users

def get_user_by_id(user_id):
    """
    Get a user by ID that works with both database schemas.
    Returns a dictionary with user data.
    """
    # Detect which dialect we're using
    dialect = db.engine.dialect.name
    
    # Get the appropriate query for the dialect
    if dialect == 'postgresql':
        # PostgreSQL query - for the 'users' table
        query = text("""
        SELECT * FROM users WHERE id = :user_id
        """)
    else:
        # SQLite query - for the 'user' table
        query = text("""
        SELECT * FROM user WHERE id = :user_id
        """)
    
    # Execute the query
    result = db.session.execute(query, {'user_id': user_id})
    row = result.fetchone()
    
    if not row:
        return None
        
    # Convert to dictionary
    user_dict = dict(row._mapping)
    
    # For SQLite, handle JSON attributes
    if dialect != 'postgresql' and 'attributes' in user_dict and user_dict['attributes']:
        try:
            user_dict['attributes'] = json.loads(user_dict['attributes'])
        except:
            pass
            
    return user_dict

def get_user_by_email(email):
    """
    Get a user by email that works with both database schemas.
    Returns a dictionary with user data.
    """
    # Detect which dialect we're using
    dialect = db.engine.dialect.name
    
    # Get the appropriate query for the dialect
    if dialect == 'postgresql':
        # PostgreSQL query - for the 'users' table
        query = text("""
        SELECT * FROM users WHERE email = :email
        """)
    else:
        # SQLite query - for the 'user' table
        query = text("""
        SELECT * FROM user WHERE email = :email
        """)
    
    # Execute the query
    result = db.session.execute(query, {'email': email})
    row = result.fetchone()
    
    if not row:
        return None
        
    # Convert to dictionary
    user_dict = dict(row._mapping)
    
    # For SQLite, handle JSON attributes
    if dialect != 'postgresql' and 'attributes' in user_dict and user_dict['attributes']:
        try:
            user_dict['attributes'] = json.loads(user_dict['attributes'])
        except:
            pass
            
    return user_dict 