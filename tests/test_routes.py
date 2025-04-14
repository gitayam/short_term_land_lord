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
            role=UserRoles.PROPERTY_OWNER.value
        )
        self.owner.set_password('password')
        
        self.staff = User(
            first_name='Test',
            last_name='Staff',
            email='staff@example.com',
            role=UserRoles.SERVICE_STAFF.value
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
            address='123 Test St, Test City, Test State 12345, Test Country',
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
            creator_id=self.owner.id,
            due_date=datetime.utcnow() + timedelta(days=1)
        )
        db.session.add(self.task)
        db.session.commit()
        
        # Link the task to the property
        task_property = TaskProperty(
            task_id=self.task.id,
            property_id=self.property.id
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
    
    def test_task_assignment(self):
        """Test assigning a task to a staff member."""
        # Login as owner
        self.login('owner@example.com', 'password')
        
        # Verify access to the assignment page
        response = self.client.get(f'/tasks/{self.task.id}/assign')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Assign Task', response.data)
    
    def test_task_creation(self):
        """Test task creation."""
        # Login as owner
        self.login('owner@example.com', 'password')
        
        # Access the task creation page
        response = self.client.get('/tasks/create')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Create New Task', response.data)


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
            role=UserRoles.PROPERTY_OWNER.value
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
            address='123 Test St, Test City, Test State 12345, Test Country',
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
        
        # View property details which includes service history
        response = self.client.get(f'/property/{self.property.id}/view')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Service History', response.data)


if __name__ == '__main__':
    unittest.main() 