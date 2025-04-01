#!/usr/bin/env python
"""
Test script for database compatibility utilities
"""
import sys
from pathlib import Path

# Add the parent directory to sys.path
parent_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(parent_dir))

from app import create_app, db
from app.utils.db_compatibility import search_users, get_user_by_id, get_user_by_email

def run_tests():
    """Test the database compatibility utilities"""
    print("Testing database compatibility utilities...")
    
    # Detect dialect
    dialect = db.engine.dialect.name
    print(f"Database dialect: {dialect}")
    
    # Test get_user_by_id
    print("\nTesting get_user_by_id...")
    user = get_user_by_id(1)
    if user:
        print(f"Found user with ID 1: {user['first_name']} {user['last_name']} ({user['email']})")
        
        # Print additional fields if available
        for field in ['username', 'authentik_id', 'signal_identity', 'is_active', 'is_admin']:
            if field in user:
                print(f"  {field}: {user[field]}")
    else:
        print("No user found with ID 1")
    
    # Test get_user_by_email
    test_email = "admin@example.com"  # Adjust based on your data
    print(f"\nTesting get_user_by_email with '{test_email}'...")
    user = get_user_by_email(test_email)
    if user:
        print(f"Found user with email '{test_email}': {user['first_name']} {user['last_name']} (ID: {user['id']})")
    else:
        print(f"No user found with email '{test_email}'")
    
    # Test search_users
    search_terms = ["admin", "example", "test"]
    for term in search_terms:
        print(f"\nTesting search_users with term '{term}'...")
        users = search_users(term)
        print(f"Found {len(users)} users matching '{term}':")
        for user in users:
            print(f"  - {user['first_name']} {user['last_name']} ({user['email']})")
    
    print("\nTests completed!")

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        run_tests() 