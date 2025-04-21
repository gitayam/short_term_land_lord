import unittest
from datetime import datetime
from io import BytesIO
from app import create_app, db
from app.models import (User, UserRoles, Task, TaskStatus, TaskPriority,
                       Property, RepairRequestSeverity)
from config import TestConfig
import os


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
            role=UserRoles.TENANT.value
        )
        self.tenant.set_password('test_password')
        
        db.session.add_all([self.owner, self.tenant])
        db.session.commit()
        
        # Create test property
        self.property = Property(
            name='Test Property',
            description='A test property',
            address='123 Test St, Test City, Test State 12345',
            street_address='123 Test St',
            city='Test City',
            state='Test State',
            zip_code='12345',
            country='Test Country',
            owner_id=self.owner.id
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
        response = self.client.get('/tasks/repair-request')
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
            'property_id': self.property.id,
            'location': 'Living Room',
            'priority': TaskPriority.HIGH.value,
            'severity': RepairRequestSeverity.URGENT.value,
            'photos': [photo],
            'notes': 'Please fix ASAP'
        }
        
        response = self.client.post('/tasks/repair-request', 
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
        self.assertEqual(len(task.photo_paths), 1)
    
    def test_repair_request_validation_errors(self):
        """Test repair request form validation"""
        # Login as tenant
        self.login('tenant@example.com', 'test_password')
        
        # Submit repair request with missing required fields
        data = {
            'description': 'Missing title and property',
            'location': 'Kitchen'
        }
        
        response = self.client.post('/tasks/repair-request',
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
            'property_id': self.property.id,
            'location': 'Bathroom',
            'priority': TaskPriority.MEDIUM.value,
            'severity': RepairRequestSeverity.MEDIUM.value,
            'photos': [large_photo]
        }
        
        response = self.client.post('/tasks/repair-request',
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
            'property_id': self.property.id,
            'location': 'Kitchen',
            'priority': TaskPriority.HIGH.value,
            'severity': RepairRequestSeverity.URGENT.value
        }
        
        self.client.post('/tasks/repair-request',
                        data=data,
                        follow_redirects=True)
        
        # Login as owner
        self.login('owner@example.com', 'test_password')
        
        # Check owner's notifications
        response = self.client.get('/notifications')
        self.assertIn(b'New repair request', response.data)
        self.assertIn(b'Urgent Repair Needed', response.data)


if __name__ == '__main__':
    unittest.main() 