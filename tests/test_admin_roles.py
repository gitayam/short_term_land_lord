#!/usr/bin/env python3
"""
Test script to verify admin role check is working correctly.
"""
import sys
from app import create_app, db
from app.models import User, UserRoles

def test_admin_roles():
    """Test if the has_admin_role method is working correctly."""
    # Create the app with a test configuration
    app = create_app()

    with app.app_context():
        # Test 1: User with is_admin=True but not ADMIN role
        user1 = User(
            username='test_admin_flag',
            email='test_admin_flag@example.com',
            role=UserRoles.PROPERTY_OWNER.value,
            is_admin=True
        )

        # Test 2: User with ADMIN role but is_admin=False
        user2 = User(
            username='test_admin_role',
            email='test_admin_role@example.com',
            role=UserRoles.ADMIN.value,
            is_admin=False
        )

        # Don't actually add these users to the database, just test the method
        print(f"Test 1 - is_admin=True, role=PROPERTY_OWNER")
        print(f"has_admin_role(): {user1.has_admin_role()}")
        print(f"Expected: True")

        print(f"\nTest 2 - is_admin=False, role=ADMIN")
        print(f"has_admin_role(): {user2.has_admin_role()}")
        print(f"Expected: True")

        # Both tests should pass if has_admin_role() works correctly
        return user1.has_admin_role() and user2.has_admin_role()

if __name__ == '__main__':
    result = test_admin_roles()
    if result:
        print("\nTest PASSED: has_admin_role() works correctly!")
        sys.exit(0)
    else:
        print("\nTest FAILED: has_admin_role() not working correctly!")
        sys.exit(1)