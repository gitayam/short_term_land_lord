#!/usr/bin/env python3
"""
Script to fix database schema issues and create an admin user manually.
"""
import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Database connection settings
DB_HOST = 'localhost'
DB_PORT = '5434'  # Port exposed in docker-compose.yml
DB_NAME = 'flask_app'
DB_USER = 'postgres'
DB_PASSWORD = 'postgres'

def connect_to_db():
    """Connect to the PostgreSQL database"""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        sys.exit(1)

def fix_users_table(conn):
    """Ensure users table has all required columns"""
    cursor = conn.cursor()
    
    # Check if phone column exists
    cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='users' AND column_name='phone'
    """)
    
    if cursor.fetchone() is None:
        print("Adding missing 'phone' column to users table...")
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN phone VARCHAR(20)")
            print("Added 'phone' column successfully")
        except Exception as e:
            print(f"Error adding phone column: {e}")
    else:
        print("'phone' column already exists")
    
    # Check if is_admin column exists with correct name
    cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='users' AND column_name='is_admin'
    """)
    
    if cursor.fetchone() is None:
        print("Adding missing 'is_admin' column to users table...")
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT FALSE")
            print("Added 'is_admin' column successfully")
        except Exception as e:
            print(f"Error adding is_admin column: {e}")
    else:
        print("'is_admin' column already exists")
    
    cursor.close()

def create_admin_user(conn):
    """Create an admin user directly in the database"""
    cursor = conn.cursor()
    
    # Check if admin user already exists
    cursor.execute("SELECT id FROM users WHERE email = 'admin@example.com'")
    admin = cursor.fetchone()
    
    if admin:
        print("Admin user already exists, updating...")
        cursor.execute("""
            UPDATE users 
            SET 
                role = 'admin',
                is_admin = TRUE,
                password_hash = 'pbkdf2:sha256:260000$Svt0rBv4J4ZiWmqf$9faea7a99cdd7b4a5d5bda3b3d40b0e5f8a8ad0db32bdff3aa1c377ccda3d6e0'
            WHERE email = 'admin@example.com'
        """)
        print("Admin user updated successfully")
    else:
        print("Creating new admin user...")
        try:
            # Insert admin user with pbkdf2:sha256 hash for 'adminpass'
            cursor.execute("""
                INSERT INTO users (
                    username, first_name, last_name, email, role, is_admin, password_hash, created_at, updated_at, is_active
                ) VALUES (
                    'admin', 'Admin', 'User', 'admin@example.com', 'admin', TRUE, 
                    'pbkdf2:sha256:260000$Svt0rBv4J4ZiWmqf$9faea7a99cdd7b4a5d5bda3b3d40b0e5f8a8ad0db32bdff3aa1c377ccda3d6e0',
                    CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, TRUE
                )
            """)
            print("Admin user created successfully")
        except Exception as e:
            print(f"Error creating admin user: {e}")
    
    cursor.close()

def main():
    """Main function"""
    conn = connect_to_db()
    fix_users_table(conn)
    create_admin_user(conn)
    conn.close()
    print("Database fixes completed!")

if __name__ == "__main__":
    main() 