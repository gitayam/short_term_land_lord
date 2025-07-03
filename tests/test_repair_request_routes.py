import unittest
from datetime import datetime
from io import BytesIO
from app import create_app, db
from app.models import (User, UserRoles, Task, TaskStatus, TaskPriority,
                       Property, RepairRequestSeverity)
from config import TestConfig
import os
from bs4 import BeautifulSoup


class TestRepairRequestRoutes(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        
        # Create test users
        self.owner = User(
            first_name='Test',
            last_name='Owner',
            email='owner@example.com',
            role=UserRoles.PROPERTY_OWNER.value
        )
        self.owner.set_password('test_password')
        
        self.tenant = User(
            first_name='Test',
            last_name='Tenant',
            email='tenant@example.com',
            role=UserRoles.PROPERTY_OWNER.value  # Make tenant a property owner for testing
        )
        self.tenant.set_password('test_password')
        
        db.session.add_all([self.owner, self.tenant])
        db.session.commit()
        
        # Create test property owned by tenant for access testing
        self.property = Property(
            name='Test Property',
            description='A test property',
            address='123 Test St, Test City, Test State 12345',
            street_address='123 Test St',
            city='Test City',
            state='Test State',
            zip_code='12345',
            country='Test Country',
            owner_id=self.tenant.id  # Make tenant the owner for testing access
        )
        
        db.session.add(self.property)
        db.session.commit()
        
        # Create uploads directory for testing
        self.upload_dir = os.path.join(self.app.root_path, 'static', 'uploads', 'repair_requests')
        os.makedirs(self.upload_dir, exist_ok=True)
    
    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def login(self, email, password):
        return self.client.post('/auth/login', data={
            'email': email,
            'password': password
        }, follow_redirects=True)
    
    def test_repair_request_form_access(self):
        """Test access to repair request form"""
        # Login as tenant
        self.login('tenant@example.com', 'test_password')
        
        # Access repair request form
        response = self.client.get(f'/tasks/repair_requests/create?property_id={self.property.id}')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Submit Repair Request', response.data)
    
    def test_repair_request_submission(self):
        """Test submitting a repair request"""
        # Login as tenant
        self.login('tenant@example.com', 'test_password')
        
        # Create test photo
        photo = (BytesIO(b'test photo content'), 'test.jpg')
        
        # Submit repair request
        data = {
            'title': 'Test Repair Request',
            'description': 'This is a test repair request',
            'property': self.property.id,
            'location': 'Living Room',
            'priority': 'HIGH',
            'severity': 'urgent_severity',
            'photos': [photo],
            'additional_notes': 'Please fix ASAP'
        }
        
        response = self.client.post(f'/tasks/repair_requests/create?property_id={self.property.id}', 
                                  data=data,
                                  content_type='multipart/form-data',
                                  follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        
        # Verify repair request was created
        task = Task.query.filter_by(title='Test Repair Request').first()
        self.assertIsNotNone(task)
        self.assertEqual(task.description, 'This is a test repair request')
        self.assertEqual(task.location, 'Living Room')
        self.assertEqual(task.priority, TaskPriority.HIGH)
        self.assertEqual(task.severity, RepairRequestSeverity.URGENT.value)
        self.assertEqual(len(task.photo_paths_list), 1)
    
    def test_repair_request_validation_errors(self):
        """Test repair request form validation"""
        # Login as tenant
        self.login('tenant@example.com', 'test_password')
        
        # Submit repair request with missing required fields
        data = {
            'description': 'Missing title and property',
            'location': 'Kitchen'
        }
        
        response = self.client.post(f'/tasks/repair_requests/create?property_id={self.property.id}',
                                  data=data,
                                  follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'This field is required', response.data)
        
        # Verify no task was created
        tasks = Task.query.all()
        self.assertEqual(len(tasks), 0)
    
    def test_repair_request_photo_validation(self):
        """Test photo upload validation"""
        # Login as tenant
        self.login('tenant@example.com', 'test_password')
        
        # Create invalid photo (too large)
        large_photo = (BytesIO(b'x' * (10 * 1024 * 1024)), 'large.jpg')  # 10MB file
        
        data = {
            'title': 'Test Photo Validation',
            'description': 'Testing photo upload validation',
            'property': self.property.id,
            'location': 'Bathroom',
            'priority': 'MEDIUM',
            'severity': 'medium_severity',
            'photos': [large_photo]
        }
        
        response = self.client.post(f'/tasks/repair_requests/create?property_id={self.property.id}',
                                  data=data,
                                  content_type='multipart/form-data',
                                  follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'File size exceeds maximum limit', response.data)
    
    def test_repair_request_notification(self):
        """Test repair request notifications"""
        # Login as tenant
        self.login('tenant@example.com', 'test_password')
        
        # Submit repair request
        data = {
            'title': 'Urgent Repair Needed',
            'description': 'Testing notifications',
            'property': self.property.id,
            'location': 'Kitchen',
            'priority': 'HIGH',
            'severity': 'urgent_severity'
        }
        
        self.client.post(f'/tasks/repair_requests/create?property_id={self.property.id}',
                        data=data,
                        follow_redirects=True)
        
        # Login as owner
        self.login('owner@example.com', 'test_password')
        
        # Check owner's notifications
        response = self.client.get('/notifications')
        self.assertIn(b'New repair request', response.data)
        self.assertIn(b'Urgent Repair Needed', response.data)

    def test_repair_request_create_route_success(self):
        """Test submitting a repair request via /tasks/repair_requests/create"""
        self.login('tenant@example.com', 'test_password')
        property_id = self.property.id
        # Get the form to get CSRF token
        response = self.client.get(f'/tasks/repair_requests/create?property_id={property_id}')
        self.assertEqual(response.status_code, 200)
        # Parse CSRF token if present
        soup = BeautifulSoup(response.data, 'html.parser')
        csrf_token = soup.find('input', {'name': 'csrf_token'})
        csrf_token_value = csrf_token['value'] if csrf_token else ''
        data = {
            'csrf_token': csrf_token_value,
            'title': 'Test Repair Request',
            'description': 'This is a test repair request',
            'property': property_id,
            'location': 'Living Room',
            'priority': 'HIGH',
            'severity': 'urgent',
            'due_date': '',
            'additional_notes': 'Please fix ASAP',
        }
        response = self.client.post(f'/tasks/repair_requests/create?property_id={property_id}',
                                    data=data,
                                    follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Repair request created successfully', response.data)
        task = Task.query.filter_by(title='Test Repair Request').first()
        self.assertIsNotNone(task)
        self.assertEqual(task.description, 'This is a test repair request')
        self.assertEqual(task.location, 'Living Room')
        self.assertEqual(task.priority.name, 'HIGH')

    def test_repair_request_create_route_validation_error(self):
        """Test submitting a repair request with missing required fields"""
        self.login('tenant@example.com', 'test_password')
        property_id = self.property.id
        response = self.client.get(f'/tasks/repair_requests/create?property_id={property_id}')
        soup = BeautifulSoup(response.data, 'html.parser')
        csrf_token = soup.find('input', {'name': 'csrf_token'})
        csrf_token_value = csrf_token['value'] if csrf_token else ''
        data = {
            'csrf_token': csrf_token_value,
            'description': 'Missing title',
            'property': property_id,
            'location': '',
            'priority': '',
            'severity': '',
        }
        response = self.client.post(f'/tasks/repair_requests/create?property_id={property_id}',
                                    data=data,
                                    follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Form validation errors', response.data)
        task = Task.query.filter_by(description='Missing title').first()
        self.assertIsNone(task)

    def test_repair_request_create_route_missing_property_id(self):
        """Test submitting a repair request with missing property_id in query string"""
        self.login('tenant@example.com', 'test_password')
        response = self.client.get('/tasks/repair_requests/create')
        self.assertEqual(response.status_code, 302)  # Should redirect
        response = self.client.post('/tasks/repair_requests/create', data={}, follow_redirects=True)
        self.assertIn(b'Property ID is required to create a repair request', response.data)


if __name__ == '__main__':
    unittest.main() 