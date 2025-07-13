#!/usr/bin/env python3
"""
Script to directly reset admin password using raw SQL.
"""
import os
import sqlite3
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

# Load environment variables from .env file
load_dotenv()

def reset_admin_password():
    """Reset the password for an admin user using direct SQL."""
    # Get admin credentials from environment
    admin_email = os.environ.get('ADMIN_EMAIL')
    admin_password = os.environ.get('ADMIN_PASSWORD')
    
    if not admin_email or not admin_password:
        print('Admin credentials not fully specified in environment variables.')
        print('Please set ADMIN_EMAIL and ADMIN_PASSWORD in your .env file.')
        return
    
    # Generate password hash
    # Using pbkdf2:sha256 for compatibility
    password_hash = generate_password_hash(admin_password)
    
    try:
        # Connect to the database
        conn = sqlite3.connect('./instance/app.db')
        cursor = conn.cursor()
        
        # First check if user exists
        cursor.execute("SELECT id, email FROM users WHERE email = ?", (admin_email,))
        user = cursor.fetchone()
        
        if not user:
            print(f"No user found with email: {admin_email}")
            return
        
        # Update password
        cursor.execute("UPDATE users SET password_hash = ? WHERE email = ?", 
                      (password_hash, admin_email))
        conn.commit()
        
        print(f"Password updated successfully for user: {admin_email}")
        print(f"You can now log in with email: {admin_email} and the password from your .env file.")
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    reset_admin_password()
