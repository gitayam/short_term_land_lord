import unittest
from flask import current_app
from app import create_app, db
from app.models import User, UserRoles
from app.user_model_fix import get_user_table_name, get_user_fk_target
from config import TestConfig

class TestDatabaseCompatibility(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        # Create a test user
        self.test_user = User(
            username='testuser',
            first_name='Test',
            last_name='User',
            email='test@example.com',
            role=UserRoles.PROPERTY_OWNER.value
        )
        self.test_user.set_password('password')
        db.session.add(self.test_user)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_user_table_name(self):
        """Test that the user table name is correctly detected"""
        table_name = get_user_table_name()
        dialect = db.engine.dialect.name

        if dialect == 'postgresql':
            self.assertEqual(table_name, 'users')
        else:
            self.assertEqual(table_name, 'user')

    def test_user_fk_target(self):
        """Test that the user foreign key target is correctly detected"""
        fk_target = get_user_fk_target()
        dialect = db.engine.dialect.name

        if dialect == 'postgresql':
            self.assertEqual(fk_target, 'users.id')
        else:
            self.assertEqual(fk_target, 'user.id')

    def test_user_loading(self):
        """Test that users can be loaded correctly"""
        from flask_login import login_user, current_user

        # Get the user from the database
        user = User.query.filter_by(email='test@example.com').first()
        self.assertIsNotNone(user)

        # Test login
        with self.app.test_request_context():
            login_user(user)
            self.assertEqual(current_user.id, user.id)
            self.assertEqual(current_user.email, 'test@example.com')

    def test_user_model_attributes(self):
        """Test that the User model has all required attributes"""
        user = User.query.filter_by(email='test@example.com').first()

        # Check basic attributes
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.first_name, 'Test')
        self.assertEqual(user.last_name, 'User')
        self.assertEqual(user.role, UserRoles.PROPERTY_OWNER.value)

        # Check that the user can be authenticated
        self.assertTrue(user.check_password('password'))
        self.assertFalse(user.check_password('wrong_password'))

    def test_search_users(self):
        """Test that the search_users function works correctly"""
        from app.utils.db_compatibility import search_users

        # Search for the test user by email
        results = search_users('test@example.com')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['email'], 'test@example.com')

        # Search for the test user by first name
        results = search_users('Test')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['first_name'], 'Test')

        # Search for a non-existent user
        results = search_users('nonexistent')
        self.assertEqual(len(results), 0)

        # Test with empty search term
        results = search_users('')
        self.assertEqual(len(results), 0)

        # Test with None search term
        results = search_users(None)
        self.assertEqual(len(results), 0)

if __name__ == '__main__':
    unittest.main()