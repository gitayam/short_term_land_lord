import unittest
from app import create_app, db
from app.models import User, Property, UserRoles
from flask_login import current_user
from flask import url_for, session
from config import TestConfig
from tests.utils import login, logout

class TestAdminPropertyPermissions(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()
        db.create_all()

        # Create admin user
        self.admin_user = User(
            username='admin',
            email='admin@example.com',
            is_admin=True,
            role=UserRoles.ADMIN.value,
            first_name='Admin',
            last_name='User'
        )
        self.admin_user.set_password('adminpassword')

        # Create property owner
        self.property_owner = User(
            username='owner',
            email='owner@example.com',
            role=UserRoles.PROPERTY_OWNER.value,
            first_name='Property',
            last_name='Owner'
        )
        self.property_owner.set_password('ownerpassword')

        # Create property
        db.session.add(self.admin_user)
        db.session.add(self.property_owner)
        db.session.commit()

        self.property = Property(
            name='Test Property',
            address='123 Test St, Test City, Test State 12345, USA',
            description='A test property',
            property_type='house',
            owner_id=self.property_owner.id
        )
        db.session.add(self.property)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_admin_can_view_any_property(self):
        """Test that admin users can view any property"""
        with self.client as c:
            # Login as admin
            login(c, 'admin@example.com', 'adminpassword')

            # Try to view property owned by someone else
            response = c.get(f'/property/{self.property.id}/view', follow_redirects=True)

            # Check that admin can access the property view
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'Test Property', response.data)

            # Logout admin
            logout(c)

    def test_property_owner_can_view_own_property(self):
        """Test that property owners can view their own properties"""
        with self.client as c:
            # Login as property owner
            login(c, 'owner@example.com', 'ownerpassword')

            # Try to view own property
            response = c.get(f'/property/{self.property.id}/view', follow_redirects=True)

            # Check that owner can access their property view
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'Test Property', response.data)

            # Logout property owner
            logout(c)

    def test_property_owner_cannot_view_others_property(self):
        """Test that property owners cannot view properties they don't own"""
        with self.client as c:
            # Create another property owner
            other_owner = User(
                username='other_owner',
                email='other_owner@example.com',
                role=UserRoles.PROPERTY_OWNER.value,
                first_name='Other',
                last_name='Owner'
            )
            other_owner.set_password('password')
            db.session.add(other_owner)
            db.session.commit()

            # Login as the other property owner
            login(c, 'other_owner@example.com', 'password')

            # Try to view property owned by someone else
            response = c.get(f'/property/{self.property.id}/view', follow_redirects=True)

            # Check that access is denied
            self.assertIn(b'You do not have permission to view this property', response.data)

            # Logout
            logout(c)

    def test_admin_is_admin_flag_works(self):
        """Test that the is_admin flag is working properly"""
        # Create a user with admin role but no is_admin flag
        admin_role_user = User(
            username='admin_role',
            email='admin_role@example.com',
            role=UserRoles.ADMIN.value,
            first_name='Admin',
            last_name='Role',
            is_admin=False  # Explicitly set to False
        )
        admin_role_user.set_password('password')
        db.session.add(admin_role_user)
        db.session.commit()

        # Check that has_admin_role() returns True despite is_admin=False
        # because the role is set to ADMIN
        self.assertTrue(admin_role_user.has_admin_role())

        # Create a user with non-admin role but is_admin flag set to True
        is_admin_user = User(
            username='is_admin',
            email='is_admin@example.com',
            role=UserRoles.PROPERTY_OWNER.value,
            first_name='Is',
            last_name='Admin',
            is_admin=True
        )
        is_admin_user.set_password('password')
        db.session.add(is_admin_user)
        db.session.commit()

        # Check that has_admin_role() returns True because is_admin=True
        # despite the role not being ADMIN
        self.assertTrue(is_admin_user.has_admin_role())

        # Also test the property getter
        self.assertTrue(is_admin_user.is_admin)
        self.assertTrue(admin_role_user.is_admin)  # This should be True because of has_admin_role()