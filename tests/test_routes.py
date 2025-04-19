import unittest
from datetime import datetime, timedelta
from app import create_app, db
from app.models import (User, UserRoles, Task, TaskAssignment, TaskStatus, 
                       TaskPriority, TaskProperty, Property, RecurrencePattern,
                       ServiceType, RepairRequest, Room, RoomFurniture)
from flask import url_for
import json
from config import TestConfig
from werkzeug.security import generate_password_hash


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
            property_id=self.property.id,
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
        
        # Access the property creation page
        response = self.client.get('/property/create')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Add Property', response.data)
        
        # Create a property
        response = self.client.post('/property/create', data={
            'name': 'New Test Property',
            'description': 'A newly created test property',
            'street_address': '456 New St',
            'city': 'New City',
            'state': 'New State',
            'zip_code': '67890',
            'country': 'New Country',
            'property_type': 'house',
            'bedrooms': 3,
            'bathrooms': 2,
            'square_feet': 1500
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Property created successfully', response.data)
        self.assertIn(b'New Test Property', response.data)
        
        # Verify property was created in database
        property = Property.query.filter_by(name='New Test Property').first()
        self.assertIsNotNone(property)
        self.assertEqual(property.bedrooms, 3)
        
    def test_property_with_rooms_and_furniture(self):
        """Test creating property with rooms and furniture."""
        # Login as owner
        self.login('owner@example.com', 'password')
        
        # Create a property with rooms and furniture
        response = self.client.post('/property/create', data={
            'name': 'Property with Rooms',
            'description': 'A property with rooms and furniture',
            'street_address': '789 Room St',
            'city': 'Room City',
            'state': 'Room State',
            'zip_code': '12345',
            'country': 'Room Country',
            'property_type': 'house',
            'bedrooms': 3,
            'bathrooms': 2,
            'square_feet': 2000,
            
            # Room data
            'room_name': ['Master Bedroom', 'Guest Bedroom'],
            'room_type': ['bedroom', 'bedroom'],
            'room_sqft': ['300', '250'],
            'has_tv': ['new_0'],  # Only first room has TV
            'tv_details': ['55-inch Samsung TV', ''],
            'bed_type': ['king', 'queen'],
            
            # Furniture data for first room
            'furniture_type_new_0[]': ['bed', 'dresser'],
            'furniture_details_new_0[]': ['Memory foam mattress', 'Wooden dresser'],
            'furniture_quantity_new_0[]': ['1', '2'],
            
            # Furniture data for second room
            'furniture_type_new_1[]': ['bed', 'chair'],
            'furniture_details_new_1[]': ['Queen size bed', 'Reading chair'],
            'furniture_quantity_new_1[]': ['1', '1']
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Property created successfully', response.data)
        
        # Verify property was created
        property = Property.query.filter_by(name='Property with Rooms').first()
        self.assertIsNotNone(property)
        
        # Verify rooms were created
        self.assertEqual(property.rooms.count(), 2)
        
        # Check first room
        room1 = property.rooms.filter_by(name='Master Bedroom').first()
        self.assertIsNotNone(room1)
        self.assertEqual(room1.room_type, 'bedroom')
        self.assertEqual(room1.square_feet, 300)
        
        # Check second room
        room2 = property.rooms.filter_by(name='Guest Bedroom').first()
        self.assertIsNotNone(room2)
        self.assertEqual(room2.room_type, 'bedroom')
        self.assertEqual(room2.square_feet, 250)
        
        # Check furniture in first room
        self.assertEqual(len(room1.room_furniture), 2)
        bed = room1.room_furniture[0] if room1.room_furniture[0].furniture_type == 'bed' else room1.room_furniture[1]
        self.assertEqual(bed.name, 'Bed')
        self.assertEqual(bed.description, 'Memory foam mattress')
        
        # Check furniture in second room
        self.assertEqual(len(room2.room_furniture), 2)
        chair = room2.room_furniture[0] if room2.room_furniture[0].furniture_type == 'chair' else room2.room_furniture[1]
        self.assertEqual(chair.name, 'Chair')
        self.assertEqual(chair.description, 'Reading chair')


if __name__ == '__main__':
    unittest.main() 