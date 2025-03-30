import unittest
from datetime import datetime, timedelta
from app import create_app, db
from app.models import (User, UserRoles, Task, TaskAssignment, TaskStatus, 
                       TaskPriority, TaskProperty, Property, RecurrencePattern,
                       ServiceType, RepairRequest)
from flask import url_for
import json


class TestTaskRoutes(unittest.TestCase):
    def setUp(self):
        # Configure the app for testing
        self.app = create_app('testing')
        self.app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing
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
            owner_id=self.owner.id
        )
        db.session.add(self.property)
        db.session.commit()
        
        # Create test tasks
        self.task = Task(
            title='Test Task',
            description='A test task',
            status=TaskStatus.PENDING,
            priority=TaskPriority.MEDIUM,
            is_recurring=False,
            recurrence_pattern=RecurrencePattern.NONE,
            creator_id=self.owner.id,
            due_date=datetime.utcnow() + timedelta(days=1)
        )
        db.session.add(self.task)
        
        # Link task to property
        self.task_property = TaskProperty(
            task=self.task,
            property=self.property
        )
        db.session.add(self.task_property)
        
        # Create assignment for the staff
        self.assignment = TaskAssignment(
            task=self.task,
            user_id=self.staff.id,
            service_type=ServiceType.CLEANING
        )
        db.session.add(self.assignment)
        db.session.commit()
    
    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def login(self, email, password):
        return self.client.post('/auth/login', data={
            'email': email,
            'password': password
        }, follow_redirects=True)
    
    def logout(self):
        return self.client.get('/auth/logout', follow_redirects=True)
    
    def test_task_index_access(self):
        """Test access to task index page."""
        # Without login, should redirect to login page
        response = self.client.get('/tasks/', follow_redirects=True)
        self.assertIn(b'Please log in to access this page', response.data)
        
        # Login as owner
        self.login('owner@example.com', 'password')
        response = self.client.get('/tasks/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Test Task', response.data)
        self.logout()
        
        # Login as staff
        self.login('staff@example.com', 'password')
        response = self.client.get('/tasks/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Test Task', response.data)
    
    def test_task_view(self):
        """Test viewing a specific task."""
        # Login as owner
        self.login('owner@example.com', 'password')
        
        # View the task
        response = self.client.get(f'/tasks/{self.task.id}')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Test Task', response.data)
        self.assertIn(b'Test Property', response.data)
        self.assertIn(b'Test Staff', response.data)  # Assigned staff
        self.logout()
        
        # Login as assigned staff
        self.login('staff@example.com', 'password')
        response = self.client.get(f'/tasks/{self.task.id}')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Test Task', response.data)
    
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
        self.assertIn(b'New Task', response.data)
        self.assertIn(b'Task created successfully', response.data)
        
        # Staff should not be able to create tasks
        self.logout()
        self.login('staff@example.com', 'password')
        response = self.client.get('/tasks/create')
        self.assertEqual(response.status_code, 302)  # Should redirect
    
    def test_task_assignment(self):
        """Test assigning a task to staff."""
        # Login as owner
        self.login('owner@example.com', 'password')
        
        # Create a new task
        new_task = Task(
            title='Assignment Test Task',
            description='A task to test assignment',
            status=TaskStatus.PENDING,
            priority=TaskPriority.MEDIUM,
            creator_id=self.owner.id
        )
        db.session.add(new_task)
        
        # Link to property
        task_property = TaskProperty(
            task=new_task,
            property=self.property
        )
        db.session.add(task_property)
        db.session.commit()
        
        # Assign to staff
        response = self.client.post(f'/tasks/{new_task.id}/assign', data={
            'assign_to_user': True,
            'user': self.staff.id,
            'service_type': ServiceType.CLEANING.value
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Task assigned successfully', response.data)
        
        # Verify assignment in database
        assignment = TaskAssignment.query.filter_by(
            task_id=new_task.id,
            user_id=self.staff.id
        ).first()
        self.assertIsNotNone(assignment)
        self.assertEqual(assignment.service_type, ServiceType.CLEANING)
    
    def test_task_completion(self):
        """Test marking a task as completed."""
        # Login as assigned staff
        self.login('staff@example.com', 'password')
        
        # Mark task as completed
        response = self.client.post(f'/tasks/{self.task.id}/complete', follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Task marked as completed', response.data)
        
        # Verify task status in database
        task = Task.query.get(self.task.id)
        self.assertEqual(task.status, TaskStatus.COMPLETED)
        self.assertIsNotNone(task.completed_at)
    
    def test_property_tasks(self):
        """Test viewing tasks for a specific property."""
        # Login as owner
        self.login('owner@example.com', 'password')
        
        # View property tasks
        response = self.client.get(f'/tasks/property/{self.property.id}')
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Test Task', response.data)
        self.assertIn(b'Test Property', response.data)
        
        # Staff should only see tasks assigned to them
        self.logout()
        self.login('staff@example.com', 'password')
        response = self.client.get(f'/tasks/property/{self.property.id}')
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Test Task', response.data)
        
        # Create another task not assigned to staff
        unassigned_task = Task(
            title='Unassigned Task',
            description='A task not assigned to staff',
            status=TaskStatus.PENDING,
            priority=TaskPriority.MEDIUM,
            creator_id=self.owner.id
        )
        db.session.add(unassigned_task)
        
        # Link to property
        task_property = TaskProperty(
            task=unassigned_task,
            property=self.property
        )
        db.session.add(task_property)
        db.session.commit()
        
        # Staff should not see the unassigned task
        response = self.client.get(f'/tasks/property/{self.property.id}')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Test Task', response.data)
        self.assertNotIn(b'Unassigned Task', response.data)


class TestPropertyRoutes(unittest.TestCase):
    def setUp(self):
        # Configure the app for testing
        self.app = create_app('testing')
        self.app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing
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
            owner_id=self.owner.id
        )
        db.session.add(self.property)
        db.session.commit()
        
        # Create test task and assign to staff
        self.task = Task(
            title='Test Task',
            description='A test task',
            status=TaskStatus.PENDING,
            priority=TaskPriority.MEDIUM,
            creator_id=self.owner.id
        )
        db.session.add(self.task)
        
        self.task_property = TaskProperty(
            task=self.task,
            property=self.property
        )
        db.session.add(self.task_property)
        
        self.assignment = TaskAssignment(
            task=self.task,
            user_id=self.staff.id
        )
        db.session.add(self.assignment)
        db.session.commit()
    
    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def login(self, email, password):
        return self.client.post('/auth/login', data={
            'email': email,
            'password': password
        }, follow_redirects=True)
    
    def logout(self):
        return self.client.get('/auth/logout', follow_redirects=True)
    
    def test_property_index_access(self):
        """Test access to property index page."""
        # Without login, should redirect to login page
        response = self.client.get('/property/', follow_redirects=True)
        self.assertIn(b'Please log in to access this page', response.data)
        
        # Login as owner
        self.login('owner@example.com', 'password')
        response = self.client.get('/property/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Test Property', response.data)
        self.logout()
        
        # Staff should be redirected as they don't have access to property index
        self.login('staff@example.com', 'password')
        response = self.client.get('/property/')
        self.assertEqual(response.status_code, 302)  # Redirect
    
    def test_property_view(self):
        """Test viewing a specific property."""
        # Login as owner
        self.login('owner@example.com', 'password')
        
        # View the property
        response = self.client.get(f'/property/{self.property.id}/view')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Test Property', response.data)
        self.assertIn(b'123 Test St', response.data)
        self.logout()
        
        # Login as assigned staff
        self.login('staff@example.com', 'password')
        response = self.client.get(f'/property/{self.property.id}/view')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Test Property', response.data)
        
        # Create a staff user with no assignments to this property
        new_staff = User(
            first_name='New',
            last_name='Staff',
            email='newstaff@example.com',
            role=UserRoles.SERVICE_STAFF
        )
        new_staff.set_password('password')
        db.session.add(new_staff)
        db.session.commit()
        
        # Login as non-assigned staff - should be denied access
        self.logout()
        self.login('newstaff@example.com', 'password')
        response = self.client.get(f'/property/{self.property.id}/view')
        self.assertEqual(response.status_code, 302)  # Redirect
    
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
            'property_type': 'House',
            'bedrooms': 3,
            'bathrooms': 2.5
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'New Property', response.data)
        self.assertIn(b'Property created successfully', response.data)
        
        # Staff should not be able to create properties
        self.logout()
        self.login('staff@example.com', 'password')
        response = self.client.get('/property/create')
        self.assertEqual(response.status_code, 302)  # Should redirect
    
    def test_service_history(self):
        """Test the service history section in property view."""
        # Add some service history
        repair_request = RepairRequest(
            property_id=self.property.id,
            reporter_id=self.staff.id,
            title='Test Repair',
            description='A test repair request',
            location='Living Room'
        )
        db.session.add(repair_request)
        db.session.commit()
        
        # Login as owner
        self.login('owner@example.com', 'password')
        
        # View the property
        response = self.client.get(f'/property/{self.property.id}/view')
        self.assertEqual(response.status_code, 200)
        
        # Check for service history
        self.assertIn(b'Service History', response.data)
        self.assertIn(b'Test Task', response.data)  # Task in service history
        self.assertIn(b'Test Repair', response.data)  # Repair request in service history


if __name__ == '__main__':
    unittest.main() 