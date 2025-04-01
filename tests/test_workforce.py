import unittest
from flask import url_for
from app import create_app, db
from app.models import User, UserRoles, Property, Task, TaskAssignment, TaskProperty
from config import TestConfig
from datetime import datetime

class TestWorkforceRoutes(unittest.TestCase):
    def setUp(self):
        # Configure the app for testing
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client(use_cookies=True)
        db.create_all()
        
        # Create a test admin
        self.admin = User(
            first_name='Admin',
            last_name='User',
            email='admin@example.com',
            role=UserRoles.ADMIN
        )
        self.admin.set_password('password')
        db.session.add(self.admin)
        
        # Create a test property owner
        self.owner = User(
            first_name='Test',
            last_name='Owner',
            email='owner@example.com',
            role=UserRoles.PROPERTY_OWNER
        )
        self.owner.set_password('password')
        db.session.add(self.owner)
        
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
    
    def test_workforce_index_access(self):
        """Test access to workforce index."""
        # Without login, should redirect to login
        response = self.client.get('/workforce/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/auth/login', response.location)
        
        # Login as admin
        self.login('admin@example.com', 'password')
        response = self.client.get('/workforce/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Workforce Management', response.data)
    
    def test_invite_worker_page(self):
        """Test worker invitation page access."""
        # Login as admin
        self.login('admin@example.com', 'password')
        
        # Access the worker invitation page
        response = self.client.get('/workforce/invite')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Invite Service Staff', response.data)
    
    def test_invite_worker(self):
        """Test worker invitation process."""
        # Login as admin
        self.login('admin@example.com', 'password')
        
        # Count users before
        users_before = User.query.count()
        
        # Submit worker invitation
        response = self.client.post('/workforce/invite', data={
            'first_name': 'New',
            'last_name': 'Worker',
            'email': 'worker@example.com',
            'service_type': 'cleaning',
            'message': 'Welcome to our team!',
            'submit': 'Send Invitation'  # Include the submit field
        })
        
        # We should get a redirect response
        self.assertEqual(response.status_code, 302)
        
        # Count users after
        users_after = User.query.count()
        self.assertEqual(users_after, users_before + 1)
        
        # Verify the worker was created
        worker = User.query.filter_by(email='worker@example.com').first()
        self.assertIsNotNone(worker)
        self.assertEqual(worker.first_name, 'New')
        self.assertEqual(worker.last_name, 'Worker')
        self.assertEqual(worker.role, UserRoles.SERVICE_STAFF)
    
    def test_assign_properties_page(self):
        """Test property assignment page access."""
        # Login as admin
        self.login('admin@example.com', 'password')
        
        # Access the property assignment page
        response = self.client.get('/workforce/assign')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Assign Properties to Worker', response.data)

if __name__ == '__main__':
    unittest.main() 