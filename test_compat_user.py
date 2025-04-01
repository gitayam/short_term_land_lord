#!/usr/bin/env python
"""
Test script for the compatibility user model
"""
import sys
from pathlib import Path

# Add the parent directory to sys.path
parent_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(parent_dir))

from app import create_app, db
from app.compat_models import CompatUser, compatible_user_search, get_user_by_id, get_user_by_email

def test_compat_user():
    print("Testing compatibility user model...")
    
    # Test getting a user by ID
    try:
        user = get_user_by_id(1)
        if user:
            print(f"Successfully retrieved user by ID: {user.id}, {user.email}, {user.get_full_name()}")
            
            # Test accessing standard columns
            print(f"Role: {user.role}")
            
            # Test accessing new columns safely
            print(f"Username: {getattr(user, 'username', 'N/A')}")
            print(f"Is Admin: {getattr(user, 'is_admin', 'N/A')}")
            print(f"Is Active: {getattr(user, 'is_active', 'N/A')}")
            print(f"Date Joined: {getattr(user, 'date_joined', 'N/A')}")
            
            # Test the helper methods
            print(f"Is admin (method): {user.is_admin()}")
        else:
            print("No user found with ID 1")
    except Exception as e:
        print(f"Error retrieving user by ID: {e}")
    
    # Test user search
    search_terms = ["admin", "test", "example"]
    for term in search_terms:
        try:
            print(f"\nSearching for '{term}'...")
            users = compatible_user_search(term)
            print(f"Found {len(users)} users matching '{term}'")
            for user in users:
                print(f"  - {user.get_full_name()} ({user.email})")
        except Exception as e:
            print(f"Error searching for '{term}': {e}")
    
    print("\nCompatibility user test completed!")

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        test_compat_user() 