#!/usr/bin/env python
"""
Manual database initialization script to create the users table directly.
This bypasses SQLAlchemy's migration system for initial setup.
"""
import os
import sys
import psycopg2
from psycopg2 import sql

def create_users_table():
    """Create the users table and other essential tables directly using psycopg2."""
    try:
        # Try using direct connection info first
        print("Attempting direct database connection...")
        # In Docker Compose environment, 'db' is the hostname of the database service
        conn = psycopg2.connect(
            dbname='postgres',
            user='postgres',
            password='postgres',
            host='db',
            port=5432
        )
        conn.autocommit = False
        print("Connected successfully using direct connection parameters")
    except Exception as direct_conn_error:
        # If direct connection fails, try using DATABASE_URL
        print(f"Direct connection failed: {direct_conn_error}, trying DATABASE_URL...")
        database_url = os.environ.get('DATABASE_URL')
        
        if not database_url:
            print("DATABASE_URL environment variable not set")
            return
        
        # Handle postgres:// vs postgresql:// scheme difference
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        
        # Parse the URL to get connection parameters
        # postgresql://username:password@hostname:port/database
        # Remove postgresql:// prefix
        connection_string = database_url.replace('postgresql://', '')
        
        # Split by @ to separate credentials from host
        credentials_host = connection_string.split('@')
        if len(credentials_host) != 2:
            print(f"Invalid DATABASE_URL format: {database_url}")
            return
        
        credentials, host_part = credentials_host
        
        # Split credentials by :
        cred_parts = credentials.split(':')
        if len(cred_parts) != 2:
            print(f"Invalid credentials format in DATABASE_URL: {database_url}")
            return
        
        username, password = cred_parts
        
        # Split host part by / to get database name
        host_parts = host_part.split('/')
        if len(host_parts) < 2:
            print(f"Invalid host format in DATABASE_URL: {database_url}")
            return
        
        host_port = host_parts[0]
        dbname = host_parts[1]
        
        # Split host_port by : if port is specified
        if ':' in host_port:
            host, port = host_port.split(':')
        else:
            host = host_port
            port = 5432  # Default PostgreSQL port
        
        try:
            # Connect to PostgreSQL
            print(f"Connecting to PostgreSQL database: {host}:{port}/{dbname}")
            conn = psycopg2.connect(
                dbname=dbname,
                user=username,
                password=password,
                host=host,
                port=port
            )
            conn.autocommit = False
        except Exception as e:
            print(f"Error connecting to database using DATABASE_URL: {e}")
            return
    
    cursor = conn.cursor()
    
    try:
        print("Creating users table...")
        
        # Check if users table exists
        cursor.execute("SELECT to_regclass('public.users')")
        if cursor.fetchone()[0] is None:
            # Create users table first
            cursor.execute("""
            CREATE TABLE users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(64) UNIQUE,
                first_name VARCHAR(64),
                last_name VARCHAR(64),
                email VARCHAR(120) UNIQUE,
                password_hash VARCHAR(128),
                role VARCHAR(20),
                created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE,
                last_login TIMESTAMP WITHOUT TIME ZONE,
                authentik_id VARCHAR(36) UNIQUE,
                signal_identity VARCHAR(36) UNIQUE,
                attributes JSONB,
                is_admin BOOLEAN DEFAULT FALSE
            )
            """)
            print("Created users table.")
        else:
            print("Users table already exists.")
        
        # Create test admin user
        cursor.execute("""
        INSERT INTO users (username, first_name, last_name, email, password_hash, role, is_admin)
        VALUES ('admin', 'Admin', 'User', 'admin@example.com', 
               'pbkdf2:sha256:600000$YGVgJhGg$11f26c636612807035a8a6ad57c5463db8cfe46c6b29bd4f3bfcbf37edbd6ab2', 
               'admin', TRUE)
        ON CONFLICT (email) DO NOTHING
        """)
        print("Created admin user (if it didn't exist).")
        
        # Commit transaction
        conn.commit()
        print("Database tables created successfully!")
        
    except Exception as e:
        conn.rollback()
        print(f"Error creating tables: {e}")
    finally:
        cursor.close()
        conn.close()
        
if __name__ == "__main__":
    create_users_table() 