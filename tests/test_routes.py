import os
import unittest
from datetime import datetime, timedelta

# Set test environment variables
os.environ['FLASK_ENV'] = 'testing'
os.environ['TESTING'] = 'True'

from flask import url_for
from app import create_app, db
from app.models import User, UserRoles, Property, RegistrationRequest, Task, TaskStatus, TaskPriority, TaskProperty
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
        self.assertEqual(len(property.rooms.all()), 2)
        
        # Check first room
        room1 = next((room for room in property.rooms if room.name == 'Master Bedroom'), None)
        self.assertIsNotNone(room1)
        self.assertEqual(room1.room_type, 'bedroom')
        self.assertEqual(room1.square_feet, 300)
        
        # Check second room
        room2 = next((room for room in property.rooms if room.name == 'Guest Bedroom'), None)
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


class TestRegistrationRoutes(unittest.TestCase):
    def setUp(self):
        # Configure the app for testing with test database
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        # Initialize the database
        with self.app.app_context():
            db.create_all()
        
        self.client = self.app.test_client(use_cookies=True)
        
    def tearDown(self):
        # Clean up the database
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
        self.app_context.pop()
    
    def test_guest_registration(self):
        """Test guest registration process"""
        # Test GET request to registration page
        with self.app.test_request_context():
            response = self.client.get(url_for('auth.register'))
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'Register', response.data)
            
            # Test POST request with valid registration data for a property owner
            registration_data = {
                'username': 'testuser',
                'email': 'test@example.com',
                'first_name': 'Test',
                'last_name': 'User',
                'password': 'testpassword123',
                'password2': 'testpassword123',
                'role': 'property_owner',
                'phone': '1234567890',
                'message': 'Test registration',
                'submit': 'Register'
            }
            
            # Print debug info
            print("\n=== Registration Test Debug Info ===")
            print(f"Sending initial POST to: {url_for('auth.register')}")
            print(f"Data: {registration_data}")
            
            # Use the test client with application context
            with self.app.test_client() as client:
                # Clear any existing flash messages
                with client.session_transaction() as sess:
                    sess.pop('_flashes', None)
                
                # Make the initial POST request (should redirect to property registration)
                response = client.post(
                    url_for('auth.register'),
                    data=registration_data,
                    follow_redirects=True
                )
                
                # Check if we were redirected to the property registration page
                self.assertEqual(response.status_code, 200)
                self.assertIn(b'Register Property', response.data)
                
                # Prepare property registration data
                property_data = {
                    'property_name': 'Test Property',
                    'property_address': '123 Test St, Test City, TS 12345',
                    'property_description': 'A test property for unit testing',
                    'submit': 'Continue with Registration'
                }
                
                # Print form validation info
                from app.auth.forms import PropertyRegistrationForm
                property_form = PropertyRegistrationForm(data=property_data)
                print("\n=== Property Form Validation ===")
                print(f"Property form valid: {property_form.validate()}")
                if not property_form.validate():
                    print("Property form errors:", property_form.errors)
                
                # Make the property registration POST request
                print("\n=== Property Registration Step ===")
                print(f"Sending POST to: {url_for('auth.register', role='property_owner', step='property')}")
                print(f"Data: {property_data}")
                
                # Get the current session data before the request
                with client.session_transaction() as sess:
                    print("\n=== Session Before Property Registration ===")
                    print(f"Session keys: {list(sess.keys())}")
                    if 'registration_data' in sess:
                        print(f"Registration data in session: {sess['registration_data']}")
                
                response = client.post(
                    url_for('auth.register', role='property_owner', step='property'),
                    data=property_data,
                    follow_redirects=True
                )
                
                # Get flash messages from the session
                with client.session_transaction() as sess:
                    flashes = sess.get('_flashes', [])
                    print("\n=== Flash Messages ===")
                    for flash in flashes:
                        print(f"{flash[0]}: {flash[1]}")
                
                # Print response info
                print(f"\nResponse status code: {response.status_code}")
                print("Response data (first 500 chars):")
                response_text = response.data.decode('utf-8', 'ignore')
                print(response_text[:500] + ('...' if len(response_text) > 500 else ''))
                
                # Check if we were redirected to login
                self.assertEqual(response.status_code, 200)  # Should be on login page
                self.assertIn(b'Sign In', response.data)
                
                # Check if the success message is in the response or in flash messages
                success_message = 'Your registration request has been submitted! An administrator will review your request soon.'
                response_text = response.data.decode('utf-8', 'ignore')
                
                # Check both the response and flash messages for the success message
                message_found = (
                    success_message in response_text or 
                    any(success_message in msg for cat, msg in flashes if cat == 'success')
                )
                
                self.assertTrue(
                    message_found,
                    f"Success message not found in response or flash messages. Response: {response_text[:200]}..."
                )
                
                # Check for success message in the response
                self.assertIn(
                    b'Your registration request has been submitted', 
                    response.data,
                    "Success message not found in response"
                )
                
                # Verify the registration request was created in the database
                with self.app.app_context():
                    from app.models import RegistrationRequest, ApprovalStatus
                    registration = RegistrationRequest.query.filter_by(email='test@example.com').first()
                    self.assertIsNotNone(registration, "Registration request not found in database")
                    self.assertEqual(registration.status, ApprovalStatus.PENDING, f"Registration status is not PENDING, got {registration.status}")

    def test_property_owner_registration(self):
        """Test property owner registration with property details"""
        with self.app.test_request_context():
            # First, submit the initial registration form
            response = self.client.post(url_for('auth.register'), data={
                'username': 'propertyowner',
                'email': 'owner@example.com',
                'first_name': 'Property',
                'last_name': 'Owner',
                'password': 'ownerpass123',
                'password2': 'ownerpass123',
                'role': 'property_owner',
                'phone': '1234567890',
                'message': 'Test property registration',
                'submit': 'Register'
            }, follow_redirects=True)
            
            # Should be redirected to property registration page
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'Register Property', response.data)
            
            # Now submit the property details
            response = self.client.post(
                url_for('auth.register', role='property_owner', step='property'),
                data={
                    'property_name': 'Test Property',
                    'property_address': '123 Test St, Test City, TS 12345',
                    'property_description': 'A test property for unit testing',
                    'submit': 'Continue with Registration'
                },
                follow_redirects=True
            )
            
            # Should be redirected to login page with success message
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'Sign In', response.data)
            
            # Check for success message in the response
            self.assertIn(
                b'Your registration request has been submitted',
                response.data,
                "Success message not found in response"
            )
            
            # Verify the registration request was created with property details
            with self.app.app_context():
                from app.models import RegistrationRequest, Property, ApprovalStatus
                
                # Check registration request
                request = RegistrationRequest.query.filter_by(email='owner@example.com').first()
                self.assertIsNotNone(request, "Registration request should exist")
                self.assertEqual(
                    request.status, 
                    ApprovalStatus.PENDING, 
                    f"Status should be PENDING, got {request.status}"
                )
                
                # Check property was created with the correct details
                prop = Property.query.filter_by(name='Test Property').first()
                self.assertIsNotNone(prop, "Property should be created")
                self.assertEqual(prop.address, '123 Test St, Test City, TS 12345')
                self.assertEqual(prop.description, 'A test property for unit testing')
                self.assertEqual(prop.status, 'inactive', "New properties should be created as 'inactive'")


if __name__ == '__main__':
    unittest.main()