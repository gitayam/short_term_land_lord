import unittest
from datetime import datetime, timedelta
from app import create_app, db
from app.models import (User, UserRoles, Task, TaskAssignment, TaskStatus, 
                       TaskPriority, TaskProperty, Property, RecurrencePattern,
                       ServiceType, RepairRequest)
from flask import url_for
import json
from config import TestConfig


class TestTaskRoutes(unittest.TestCase):
    def setUp(self):
        # Configure the app for testing
        self.app = create_app(TestConfig)  # Use TestConfig for testing
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client(use_cookies=True)
        db.create_all()
        
        # Create test users
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
        
        db.session.add_all([self.owner, self.staff])
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
        
        # Create a test task
        self.task = Task(
            title='Test Task',
            description='A test task',
            status=TaskStatus.PENDING,
            priority=TaskPriority.MEDIUM,
            created_by=self.owner,
            due_date=datetime.utcnow() + timedelta(days=1)
        )
        db.session.add(self.task)
        
        # Link the task to the property
        task_property = TaskProperty(
            task=self.task,
            property=self.property
        )
        db.session.add(task_property)
        db.session.commit()
    
    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def login(self, email, password):
        """Helper method to log in."""
        return self.client.post('/auth/login', data={
            'email': email,
            'password': password
        }, follow_redirects=True)
    
    def test_task_index_access(self):
        """Test access to task index."""
        # Without login, should redirect to login
        response = self.client.get('/tasks/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/auth/login', response.location)
        
        # Login as owner
        self.login('owner@example.com', 'password')
        response = self.client.get('/tasks/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Tasks', response.data)
    
    def test_task_view(self):
        """Test viewing a specific task."""
        # Login as owner
        self.login('owner@example.com', 'password')
    
        # View the task
        response = self.client.get(f'/tasks/{self.task.id}')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Test Task', response.data)
        self.assertIn(b'Test Property', response.data)
        
        # Check for task status
        self.assertIn(b'Pending', response.data)
    
    def test_task_creation(self):
        """Test task creation."""
        # Login as owner
        self.login('owner@example.com', 'password')
    
        # Create a new task
        response = self.client.post('/tasks/create', data={
            'title': 'New Task',
            'description': 'A new test task',
            'properties': [self.property.id],
            'status': TaskStatus.PENDING.value,
            'priority': TaskPriority.HIGH.value,
            'due_date': (datetime.utcnow() + timedelta(days=2)).strftime('%Y-%m-%d'),
            'is_recurring': False,
            'recurrence_pattern': RecurrencePattern.NONE.value,
            'recurrence_interval': 1,
            'linked_to_checkout': False,
            'assign_to_next_cleaner': False,
            'calendar_id': -1  # No calendar
        }, follow_redirects=True)
    
        self.assertEqual(response.status_code, 200)
        
        # Verify the task was created in the database
        task = Task.query.filter_by(title='New Task').first()
        self.assertIsNotNone(task)
        self.assertEqual(task.description, 'A new test task')
        self.assertEqual(task.status, TaskStatus.PENDING)
        self.assertEqual(task.priority, TaskPriority.HIGH)
        
        # Verify the task is linked to the property
        self.assertEqual(len(task.properties), 1)
        self.assertEqual(task.properties[0].property.id, self.property.id)
    
    def test_task_assignment(self):
        """Test assigning a task to a staff member."""
        # Login as owner
        self.login('owner@example.com', 'password')
        
        # Assign task to staff
        response = self.client.post(f'/tasks/{self.task.id}/assign', data={
            'user_id': self.staff.id,
            'role': 'cleaner'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        
        # Verify assignment in the database
        assignment = TaskAssignment.query.filter_by(
            task_id=self.task.id,
            user_id=self.staff.id
        ).first()
        
        self.assertIsNotNone(assignment)
        self.assertEqual(assignment.role, 'cleaner')


class TestPropertyRoutes(unittest.TestCase):
    def setUp(self):
        # Configure the app for testing
        self.app = create_app(TestConfig)  # Use TestConfig for testing
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client(use_cookies=True)
        db.create_all()
        
        # Create a test owner
        self.owner = User(
            first_name='Test',
            last_name='Owner',
            email='owner@example.com',
            role=UserRoles.PROPERTY_OWNER
        )
        self.owner.set_password('password')
        db.session.add(self.owner)
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
    
    def login(self, email, password):
        """Helper method to log in."""
        return self.client.post('/auth/login', data={
            'email': email,
            'password': password
        }, follow_redirects=True)
    
    def test_property_index_access(self):
        """Test access to property index."""
        # Without login, should redirect to login
        response = self.client.get('/property/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/auth/login', response.location)
        
        # Login as owner
        self.login('owner@example.com', 'password')
        response = self.client.get('/property/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'My Properties', response.data)
    
    def test_property_view(self):
        """Test viewing a property."""
        # Login as owner
        self.login('owner@example.com', 'password')
        
        # View the property
        response = self.client.get(f'/property/{self.property.id}/view')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Test Property', response.data)
        self.assertIn(b'123 Test St', response.data)
    
    def test_property_creation(self):
        """Test property creation."""
        # Login as owner
        self.login('owner@example.com', 'password')
    
        # Create a new property
        response = self.client.post('/property/create', data={
            'name': 'New Property',
            'description': 'A new test property',
            'street_address': '456 New St',
            'city': 'New City',
            'state': 'New State',
            'zip_code': '67890',
            'country': 'New Country',
            'property_type': 'house',
            'bedrooms': 3,
            'bathrooms': 2.5
        }, follow_redirects=True)
    
        self.assertEqual(response.status_code, 200)
        
        # Verify the property was created in the database
        property = Property.query.filter_by(name='New Property').first()
        self.assertIsNotNone(property)
        self.assertEqual(property.description, 'A new test property')
        self.assertEqual(property.street_address, '456 New St')
        self.assertEqual(property.owner, self.owner)
    
    def test_service_history(self):
        """Test viewing service history."""
        # Login as owner
        self.login('owner@example.com', 'password')
        
        # View service history
        response = self.client.get(f'/property/{self.property.id}/service-history')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Service History', response.data)


if __name__ == '__main__':
    unittest.main() 