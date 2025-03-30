import unittest
from datetime import datetime, timedelta
from app import create_app, db
from app.models import User, UserRoles, Task, TaskAssignment, TaskStatus, TaskPriority, TaskProperty, Property, RecurrencePattern
from flask import current_app
import os
from config import TestConfig


class TestUserModel(unittest.TestCase):
    def setUp(self):
        # Configure the app for testing
        self.app = create_app(TestConfig)  # Use TestConfig for testing
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        
        # Create a test user for each role
        self.owner = User(
            first_name='Test',
            last_name='Owner',
            email='owner@example.com',
            role=UserRoles.PROPERTY_OWNER
        )
        self.owner.set_password('password')
        
        self.staff = User(
            first_name='Test',
            last_name='Staff',
            email='staff@example.com',
            role=UserRoles.SERVICE_STAFF
        )
        self.staff.set_password('password')
        
        self.manager = User(
            first_name='Test',
            last_name='Manager',
            email='manager@example.com',
            role=UserRoles.PROPERTY_MANAGER
        )
        self.manager.set_password('password')
        
        self.admin = User(
            first_name='Test',
            last_name='Admin',
            email='admin@example.com',
            role=UserRoles.ADMIN
        )
        self.admin.set_password('password')
        
        db.session.add_all([self.owner, self.staff, self.manager, self.admin])
        db.session.commit()
    
    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def test_password_hashing(self):
        """Test password hashing and verification."""
        self.assertTrue(self.owner.check_password('password'))
        self.assertFalse(self.owner.check_password('wrong_password'))
    
    def test_user_roles(self):
        """Test role verification methods."""
        # Owner checks
        self.assertTrue(self.owner.is_property_owner())
        self.assertFalse(self.owner.is_service_staff())
        self.assertFalse(self.owner.is_property_manager())
        self.assertFalse(self.owner.is_admin())
        
        # Staff checks
        self.assertFalse(self.staff.is_property_owner())
        self.assertTrue(self.staff.is_service_staff())
        self.assertFalse(self.staff.is_property_manager())
        self.assertFalse(self.staff.is_admin())
        
        # Manager checks
        self.assertFalse(self.manager.is_property_owner())
        self.assertFalse(self.manager.is_service_staff())
        self.assertTrue(self.manager.is_property_manager())
        self.assertFalse(self.manager.is_admin())
        
        # Admin checks
        self.assertFalse(self.admin.is_property_owner())
        self.assertFalse(self.admin.is_service_staff())
        self.assertFalse(self.admin.is_property_manager())
        self.assertTrue(self.admin.is_admin())
    
    def test_legacy_methods(self):
        """Test legacy compatibility methods."""
        self.assertTrue(self.staff.is_cleaner())
        self.assertTrue(self.staff.is_maintenance())
    
    def test_can_complete_task(self):
        """Test task completion permissions."""
        # Create a property
        property = Property(
            name='Test Property',
            description='A test property',
            street_address='123 Test St',
            city='Test City',
            state='Test State',
            zip_code='12345',
            country='Test Country',
            owner_id=self.owner.id
        )
        db.session.add(property)
        
        # Create a task
        task = Task(
            title='Test Task',
            description='A test task',
            status=TaskStatus.PENDING,
            priority=TaskPriority.MEDIUM,
            is_recurring=False,
            recurrence_pattern=RecurrencePattern.NONE,
            creator_id=self.owner.id
        )
        db.session.add(task)
        
        # Link task to property
        task_property = TaskProperty(
            task=task,
            property=property
        )
        db.session.add(task_property)
        
        # Create assignment for the staff
        assignment = TaskAssignment(
            task=task,
            user_id=self.staff.id
        )
        db.session.add(assignment)
        db.session.commit()
        
        # Verify completion permissions
        # Creator can complete
        self.assertTrue(self.owner.can_complete_task(task))
        # Assigned staff can complete
        self.assertTrue(self.staff.can_complete_task(task))
        # Unassigned staff cannot complete
        new_staff = User(
            first_name='New',
            last_name='Staff',
            email='newstaff@example.com',
            role=UserRoles.SERVICE_STAFF
        )
        db.session.add(new_staff)
        db.session.commit()
        self.assertFalse(new_staff.can_complete_task(task))
        # Admin can complete any task
        self.assertTrue(self.admin.can_complete_task(task))
    
    def test_get_full_name(self):
        """Test the get_full_name method."""
        self.assertEqual(self.owner.get_full_name(), 'Test Owner')


class TestPropertyModel(unittest.TestCase):
    def setUp(self):
        # Configure the app for testing
        self.app = create_app(TestConfig)  # Use TestConfig for testing
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        
        # Create a test user for each role
        self.owner = User(
            first_name='Test',
            last_name='Owner',
            email='owner@example.com',
            role=UserRoles.PROPERTY_OWNER
        )
        self.owner.set_password('password')
        
        self.staff = User(
            first_name='Test',
            last_name='Staff',
            email='staff@example.com',
            role=UserRoles.SERVICE_STAFF
        )
        self.staff.set_password('password')
        
        self.manager = User(
            first_name='Test',
            last_name='Manager',
            email='manager@example.com',
            role=UserRoles.PROPERTY_MANAGER
        )
        self.manager.set_password('password')
        
        self.admin = User(
            first_name='Test',
            last_name='Admin',
            email='admin@example.com',
            role=UserRoles.ADMIN
        )
        self.admin.set_password('password')
        
        db.session.add_all([self.owner, self.staff, self.manager, self.admin])
        db.session.commit()
        
        # Create a test property
        self.property = Property(
            name='Test Property',
            description='A test property',
            street_address='123 Test St',
            city='Test City',
            state='Test State',
            zip_code='12345',
            country='Test Country',
            owner=self.owner
        )
        db.session.add(self.property)
        db.session.commit()
        
    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def test_property_creation(self):
        """Test property creation."""
        # Property should exist in the database
        property_in_db = Property.query.filter_by(name='Test Property').first()
        self.assertIsNotNone(property_in_db)
        self.assertEqual(property_in_db.name, 'Test Property')
        self.assertEqual(property_in_db.description, 'A test property')
        self.assertEqual(property_in_db.owner, self.owner)
    
    def test_get_full_address(self):
        """Test getting the full address."""
        expected_address = '123 Test St, Test City, Test State 12345, Test Country'
        self.assertEqual(self.property.get_full_address(), expected_address)
    
    def test_is_visible_to(self):
        """Test the is_visible_to method."""
        # Owner can see their property
        self.assertTrue(self.property.is_visible_to(self.owner))
        
        # Configure property to not be visible to staff
        self.property.visible_to_all_staff = False
        db.session.commit()
        
        # Staff can't see property after setting visibility
        self.assertFalse(self.property.is_visible_to(self.staff))
        
        # Admin can see all properties
        self.assertTrue(self.property.is_visible_to(self.admin))
    
    def test_property_relationships(self):
        """Test property relationships."""
        # Create a task for this property
        task = Task(
            title='Test Task',
            description='A test task',
            status=TaskStatus.PENDING,
            priority=TaskPriority.MEDIUM,
            created_by=self.owner,
            due_date=datetime.utcnow() + timedelta(days=1)
        )
        db.session.add(task)
        
        # Link the task to the property
        task_property = TaskProperty(task=task, property=self.property)
        db.session.add(task_property)
        db.session.commit()
        
        # Property should have the task
        self.assertEqual(len(self.property.tasks), 1)
        self.assertEqual(self.property.tasks[0].task.title, 'Test Task')
        
        # Task should have the property
        self.assertEqual(len(task.properties), 1)
        self.assertEqual(task.properties[0].property.name, 'Test Property')
    
    def test_guest_access_token(self):
        """Test generating guest access token."""
        # Initially no token
        self.assertIsNone(self.property.guest_access_token)
    
        # Generate a token
        token = self.property.generate_guest_access_token()
        self.assertIsNotNone(token)
        self.assertEqual(token, self.property.guest_access_token)
    
        # Token should be at least 32 chars
        self.assertGreaterEqual(len(token), 32)


if __name__ == '__main__':
    unittest.main() 