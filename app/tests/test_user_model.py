"""
Tests for the User model to ensure all functionality works correctly.
"""

import unittest
from datetime import datetime
from flask import current_app
from app import create_app, db
from app.models import User, UserRoles
from config import TestConfig

class TestUserModel(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        
    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
        
    def test_password_hashing(self):
        """Test password hashing and verification"""
        u = User(
            username='test',
            first_name='Test',
            last_name='User',
            email='test@example.com',
            role=UserRoles.PROPERTY_OWNER.value
        )
        u.set_password('password')
        self.assertTrue(u.check_password('password'))
        self.assertFalse(u.check_password('wrong_password'))
        
    def test_user_creation(self):
        """Test user creation and database persistence"""
        u = User(
            username='test',
            first_name='Test',
            last_name='User',
            email='test@example.com',
            role=UserRoles.PROPERTY_OWNER.value
        )
        u.set_password('password')
        db.session.add(u)
        db.session.commit()
        
        # Retrieve the user from the database
        user = User.query.filter_by(email='test@example.com').first()
        self.assertIsNotNone(user)
        self.assertEqual(user.username, 'test')
        self.assertEqual(user.first_name, 'Test')
        self.assertEqual(user.last_name, 'User')
        self.assertEqual(user.role, UserRoles.PROPERTY_OWNER.value)
        
    def test_user_roles(self):
        """Test user role verification methods"""
        # Create users with different roles
        owner = User(
            username='owner',
            first_name='Property',
            last_name='Owner',
            email='owner@example.com',
            role=UserRoles.PROPERTY_OWNER.value
        )
        
        staff = User(
            username='staff',
            first_name='Service',
            last_name='Staff',
            email='staff@example.com',
            role=UserRoles.SERVICE_STAFF.value
        )
        
        manager = User(
            username='manager',
            first_name='Property',
            last_name='Manager',
            email='manager@example.com',
            role=UserRoles.PROPERTY_MANAGER.value
        )
        
        admin = User(
            username='admin',
            first_name='Admin',
            last_name='User',
            email='admin@example.com',
            role=UserRoles.ADMIN.value,
            is_admin=True
        )
        
        # Test role verification
        self.assertTrue(owner.is_property_owner())
        self.assertFalse(staff.is_property_owner())
        self.assertFalse(manager.is_property_owner())
        self.assertFalse(admin.is_property_owner())
        
        # Test admin flag
        self.assertFalse(owner.is_admin)
        self.assertFalse(staff.is_admin)
        self.assertFalse(manager.is_admin)
        self.assertTrue(admin.is_admin)
        
    def test_get_full_name(self):
        """Test get_full_name method"""
        u = User(
            username='test',
            first_name='Test',
            last_name='User',
            email='test@example.com'
        )
        self.assertEqual(u.get_full_name(), 'Test User')
        
        # Test with empty first name
        u = User(
            username='test',
            first_name='',
            last_name='User',
            email='test@example.com'
        )
        self.assertEqual(u.get_full_name(), 'User')
        
        # Test with empty last name
        u = User(
            username='test',
            first_name='Test',
            last_name='',
            email='test@example.com'
        )
        self.assertEqual(u.get_full_name(), 'Test')
        
    def test_timestamps(self):
        """Test that timestamps are set correctly"""
        u = User(
            username='test',
            first_name='Test',
            last_name='User',
            email='test@example.com'
        )
        db.session.add(u)
        db.session.commit()
        
        self.assertIsNotNone(u.created_at)
        self.assertIsNotNone(u.updated_at)
        
        # Test that updated_at is updated when the user is modified
        original_updated_at = u.updated_at
        u.first_name = 'Updated'
        db.session.commit()
        
        self.assertNotEqual(u.updated_at, original_updated_at)
        
    def test_last_login(self):
        """Test that last_login is updated correctly"""
        u = User(
            username='test',
            first_name='Test',
            last_name='User',
            email='test@example.com'
        )
        db.session.add(u)
        db.session.commit()
        
        self.assertIsNone(u.last_login)
        
        # Update last_login
        u.last_login = datetime.utcnow()
        db.session.commit()
        
        self.assertIsNotNone(u.last_login)
        
if __name__ == '__main__':
    unittest.main()
