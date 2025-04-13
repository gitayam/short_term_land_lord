"""
Database compatibility utilities

This module provides functions to work with both SQLite and PostgreSQL databases,
handling schema differences transparently.
"""
import json
from sqlalchemy import text, inspect
from flask import current_app

from app import db

def get_user_table_name():
    """Return the user table name - always 'users' now"""
    return 'users'

def search_users(search_term, limit=10):
    """
    Search for users with a consistent table name.
    This function searches for users by name, email, or username.
    
    Args:
        search_term: The search term to look for
        limit: Maximum number of results to return
        
    Returns:
        List of user dictionaries
    """
    # Always use 'users' table 
    table_name = 'users'
    
    try:
        # Check if the attributes column exists
        inspector = inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns(table_name)]
        has_attributes = 'attributes' in columns
        
        # Build the SQL query with proper LIKE syntax for case-insensitive search
        select_columns = "id, username, first_name, last_name, email, role"
        if has_attributes:
            select_columns += ", attributes"
            
        sql = text(f"""
        SELECT {select_columns}
        FROM {table_name} 
        WHERE lower(first_name) LIKE lower(:search) 
        OR lower(last_name) LIKE lower(:search)
        OR lower(email) LIKE lower(:search)
        OR lower(username) LIKE lower(:search)
        LIMIT :limit
        """)
        
        # Execute the query with parameters
        result = db.session.execute(sql, {
            'search': f'%{search_term}%',
            'limit': limit
        })
        
        # Convert the result to a list of dictionaries
        users = []
        for row in result:
            user_dict = {
                'id': row.id,
                'username': row.username,
                'first_name': row.first_name,
                'last_name': row.last_name,
                'email': row.email,
                'role': row.role
            }
            
            # Try to parse attributes JSON if the column exists
            if has_attributes and hasattr(row, 'attributes') and row.attributes:
                try:
                    user_dict['attributes'] = json.loads(row.attributes) if isinstance(row.attributes, str) else row.attributes
                except:
                    user_dict['attributes'] = {}
            
            users.append(user_dict)
        
        # Debug log
        current_app.logger.debug(f"Found {len(users)} users for search term: {search_term}")
        
        return users
    except Exception as e:
        current_app.logger.error(f"Error searching users: {e}")
        return []

def get_user_by_id(user_id):
    """
    Get a user by ID using a consistent table name.
    
    Args:
        user_id: The user ID to look for
        
    Returns:
        User dictionary or None
    """
    # Always use 'users' table
    table_name = 'users'
    
    try:
        # Check if the attributes column exists
        inspector = inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns(table_name)]
        has_attributes = 'attributes' in columns
        
        # Build the SQL query
        select_columns = "id, username, first_name, last_name, email, role, is_admin, is_active"
        if has_attributes:
            select_columns += ", attributes"
            
        sql = text(f"""
        SELECT {select_columns}
        FROM {table_name} 
        WHERE id = :user_id
        """)
        
        # Execute the query with parameters
        result = db.session.execute(sql, {'user_id': user_id})
        row = result.fetchone()
        
        if not row:
            return None
        
        # Convert the result to a dictionary
        user_dict = {
            'id': row.id,
            'username': row.username,
            'first_name': row.first_name,
            'last_name': row.last_name,
            'email': row.email,
            'role': row.role,
            'is_admin': row.is_admin,
            'is_active': row.is_active
        }
        
        # Try to parse attributes JSON if the column exists
        if has_attributes and hasattr(row, 'attributes') and row.attributes:
            try:
                user_dict['attributes'] = json.loads(row.attributes) if isinstance(row.attributes, str) else row.attributes
            except:
                user_dict['attributes'] = {}
        
        return user_dict
    except Exception as e:
        current_app.logger.error(f"Error getting user by ID: {e}")
        return None

def get_user_by_email(email):
    """
    Get a user by email using a consistent table name.
    
    Args:
        email: The email to look for
        
    Returns:
        User dictionary or None
    """
    # Always use 'users' table
    table_name = 'users'
    
    try:
        # Check if the attributes column exists
        inspector = inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns(table_name)]
        has_attributes = 'attributes' in columns
        
        # Build the SQL query
        select_columns = "id, username, first_name, last_name, email, role, is_admin, is_active"
        if has_attributes:
            select_columns += ", attributes"
            
        sql = text(f"""
        SELECT {select_columns}
        FROM {table_name} 
        WHERE email = :email
        """)
        
        # Execute the query with parameters
        result = db.session.execute(sql, {'email': email})
        row = result.fetchone()
        
        if not row:
            return None
        
        # Convert the result to a dictionary
        user_dict = {
            'id': row.id,
            'username': row.username,
            'first_name': row.first_name,
            'last_name': row.last_name,
            'email': row.email,
            'role': row.role,
            'is_admin': row.is_admin,
            'is_active': row.is_active
        }
        
        # Try to parse attributes JSON if the column exists
        if has_attributes and hasattr(row, 'attributes') and row.attributes:
            try:
                user_dict['attributes'] = json.loads(row.attributes) if isinstance(row.attributes, str) else row.attributes
            except:
                user_dict['attributes'] = {}
        
        return user_dict
    except Exception as e:
        current_app.logger.error(f"Error getting user by email: {e}")
        return None