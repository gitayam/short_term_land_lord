#!/usr/bin/env python3
from app import create_app, db
from app.models import User, UserRoles
import sys

"""
This script tests if admin users are correctly recognized by the has_admin_role method
after our fix to the circular reference issue.
"""

def test_admin_role():
    app = create_app()
    with app.app_context():
        print("Starting admin role test")
        
        # Create test users
        print("Creating test users...")
        
        # Create admin via role
        admin_by_role = User(
            email='admin_by_role@example.com',
            first_name='Admin',
            last_name='ByRole',
            role=UserRoles.ADMIN.value
        )
        print(f"Created admin_by_role with role={admin_by_role.role}")
        
        # Create admin via is_admin flag
        admin_by_flag = User(
            email='admin_by_flag@example.com',
            first_name='Admin',
            last_name='ByFlag',
            role=UserRoles.PROPERTY_OWNER.value
        )
        # Set is_admin after creation to trigger the setter
        admin_by_flag.is_admin = True
        print(f"Created admin_by_flag with role={admin_by_flag.role}")
        
        # Create non-admin user
        regular_user = User(
            email='regular@example.com',
            first_name='Regular',
            last_name='User',
            role=UserRoles.PROPERTY_OWNER.value
        )
        print(f"Created regular_user with role={regular_user.role}")
        
        # Add to session but don't commit to avoid DB changes
        db.session.add_all([admin_by_role, admin_by_flag, regular_user])
        
        try:
            db.session.flush()
            
            # Print direct access to __dict__ for debugging
            print("\nInternal state:")
            print(f"admin_by_role.__dict__['is_admin'] = {admin_by_role.__dict__.get('is_admin')}")
            print(f"admin_by_flag.__dict__['is_admin'] = {admin_by_flag.__dict__.get('is_admin')}")
            print(f"regular_user.__dict__['is_admin'] = {regular_user.__dict__.get('is_admin')}")
            
            # Test has_admin_role method
            print("\nTesting has_admin_role method:")
            print(f"Admin by role has admin role: {admin_by_role.has_admin_role}")
            print(f"Admin by flag has admin role: {admin_by_flag.has_admin_role}")
            print(f"Regular user has admin role: {regular_user.has_admin_role}")
            
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
        finally:
            # Rollback to avoid making actual changes to DB
            db.session.rollback()
        
if __name__ == '__main__':
    test_admin_role() 