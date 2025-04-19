import unittest
from datetime import datetime, timedelta
from app import create_app, db
from app.models import User, UserRoles, Task, TaskAssignment, TaskStatus, TaskPriority, TaskProperty, Property, RecurrencePattern, ServiceType, Room, RoomFurniture
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
        
        self.manager = User(
            first_name='Test',
            last_name='Manager',
            email='manager@example.com',
            role=UserRoles.PROPERTY_MANAGER.value
        )
        self.manager.set_password('password')
        
        self.admin = User(
            first_name='Test',
            last_name='Admin',
            email='admin@example.com',
            role=UserRoles.ADMIN.value
        )
        self.admin.set_password('password')
        
        db.session.add_all([self.owner, self.staff, self.manager, self.admin])
        db.session.commit()
        
        # Create a test property
        self.property = Property(
            name='Test Property',
            description='A test property',
            address='123 Test St, Test City, Test State 12345, Test Country',
            street_address='123 Test St',
            city='Test City',
            state='Test State',
            zip_code='12345',
            country='Test Country',
            owner_id=self.owner.id
        )
        db.session.add(self.property)
        db.session.commit()
        
        # Create a task
        self.task = Task(
            title='Test Task',
            description='A test task',
            status=TaskStatus.PENDING,
            priority=TaskPriority.MEDIUM,
            creator_id=self.owner.id,
            property_id=self.property.id
        )
        db.session.add(self.task)
        db.session.commit()
        
        # Link task to property
        self.task_property = TaskProperty(
            task_id=self.task.id,
            property_id=self.property.id
        )
        db.session.add(self.task_property)
        
        # Create cleaning assignment for the staff
        self.cleaning_assignment = TaskAssignment(
            task_id=self.task.id,
            user_id=self.staff.id,
            service_type=ServiceType.CLEANING
        )
        db.session.add(self.cleaning_assignment)
        
        # Create maintenance assignment for the staff
        self.maintenance_assignment = TaskAssignment(
            task=self.task,
            user_id=self.staff.id,
            service_type=ServiceType.HANDYMAN
        )
        db.session.add(self.maintenance_assignment)
        
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
        self.assertFalse(self.owner.is_admin)
        
        # Staff checks
        self.assertFalse(self.staff.is_property_owner())
        self.assertTrue(self.staff.is_service_staff())
        self.assertFalse(self.staff.is_property_manager())
        self.assertFalse(self.staff.is_admin)
        
        # Manager checks
        self.assertFalse(self.manager.is_property_owner())
        self.assertFalse(self.manager.is_service_staff())
        self.assertTrue(self.manager.is_property_manager())
        self.assertFalse(self.manager.is_admin)
        
        # Admin checks
        self.assertFalse(self.admin.is_property_owner())
        self.assertFalse(self.admin.is_service_staff())
        self.assertFalse(self.admin.is_property_manager())
        self.assertTrue(self.admin.is_admin)
    
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
            address='123 Test St, Test City, Test State 12345, Test Country',
            owner_id=self.owner.id
        )
        db.session.add(property)
        db.session.commit()  # Commit to get a valid property.id before creating Task
        
        # Create a task with property_id
        task = Task(
            title='Test Task',
            description='A test task',
            status=TaskStatus.PENDING,
            priority=TaskPriority.MEDIUM,
            is_recurring=False,
            recurrence_pattern=RecurrencePattern.NONE,
            creator_id=self.owner.id,
            property_id=property.id  # Set the property_id
        )
        db.session.add(task)
        db.session.commit()
        
        # Link task to property
        task_property = TaskProperty(
            task_id=task.id,
            property_id=property.id
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
            role=UserRoles.SERVICE_STAFF.value
        )
        db.session.add(new_staff)
        db.session.commit()
        self.assertFalse(new_staff.can_complete_task(task))
        # Admin can complete any task
        self.assertTrue(self.admin.can_complete_task(task))
    
    def test_get_full_name(self):
        """Test the get_full_name method."""
        self.assertEqual(self.owner.get_full_name(), 'Test Owner')

    def test_can_reassign_task(self):
        """Test task reassignment permissions."""
        # Create a property
        property = Property(
            name='Test Property',
            description='A test property',
            street_address='123 Test St',
            city='Test City',
            state='Test State',
            zip_code='12345',
            country='Test Country',
            address='123 Test St, Test City, Test State 12345, Test Country',
            owner_id=self.owner.id
        )
        db.session.add(property)
        db.session.commit()  # Commit to get a valid property.id
        
        # Create a task with property_id
        task = Task(
            title='Test Task',
            description='A test task',
            status=TaskStatus.PENDING,
            priority=TaskPriority.MEDIUM,
            is_recurring=False,
            recurrence_pattern=RecurrencePattern.NONE,
            creator_id=self.owner.id,
            property_id=property.id  # Set the property_id
        )
        db.session.add(task)
        db.session.commit()
        
        # Link task to property
        task_property = TaskProperty(
            task_id=task.id,
            property_id=property.id
        )
        db.session.add(task_property)
        
        # Create assignment for the staff
        assignment = TaskAssignment(
            task=task,
            user_id=self.staff.id
        )
        db.session.add(assignment)
        db.session.commit()
        
        # Verify reassignment permissions
        # Creator can reassign
        self.assertTrue(self.owner.can_reassign_task(task))
        # Staff cannot reassign
        self.assertFalse(self.staff.can_reassign_task(task))
        # Admin can reassign
        self.assertTrue(self.admin.can_reassign_task(task))


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
        
        self.manager = User(
            first_name='Test',
            last_name='Manager',
            email='manager@example.com',
            role=UserRoles.PROPERTY_MANAGER.value
        )
        self.manager.set_password('password')
        
        self.admin = User(
            first_name='Test',
            last_name='Admin',
            email='admin@example.com',
            role=UserRoles.ADMIN.value
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
            address='123 Test St, Test City, Test State 12345, Test Country',
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
        
        # Staff initially might be able to see property based on model implementation
        initial_visibility = self.property.is_visible_to(self.staff)
    
        # Create a task for the property
        task = Task(
            title='Test Task',
            description='A test task',
            status=TaskStatus.PENDING,
            priority=TaskPriority.MEDIUM,
            creator_id=self.owner.id,
            property_id=self.property.id,
            due_date=datetime.utcnow() + timedelta(days=1)
        )
        db.session.add(task)
        db.session.commit()  # Commit to get a valid task.id before creating TaskProperty
        
        # Link the task to the property
        task_property = TaskProperty(
            task_id=task.id,
            property_id=self.property.id
        )
        db.session.add(task_property)
        
        # Assign the task to the staff user
        assignment = TaskAssignment(
            task=task,
            user_id=self.staff.id
        )
        db.session.add(assignment)
        db.session.commit()
        
        # After assigning a task, staff should definitely be able to see the property
        self.assertTrue(self.property.is_visible_to(self.staff))
    
    def test_property_relationships(self):
        """Test property relationships."""
        # Create a task for this property
        task = Task(
            title='Test Task',
            description='A test task',
            status=TaskStatus.PENDING,
            priority=TaskPriority.MEDIUM,
            creator_id=self.owner.id,
            property_id=self.property.id,
            due_date=datetime.utcnow() + timedelta(days=1)
        )
        db.session.add(task)
        db.session.commit()  # Commit to get a valid task.id before creating TaskProperty
    
        # Link the task to the property
        task_property = TaskProperty(
            task_id=task.id,
            property_id=self.property.id
        )
        db.session.add(task_property)
        db.session.commit()
    
        # Property should have the task
        self.assertEqual(len(self.property.tasks), 1)
        self.assertEqual(self.property.tasks[0].task.title, 'Test Task')
    
        # Task should have the property
        self.assertEqual(len(task.properties), 1)
        self.assertEqual(task.properties[0].name, 'Test Property')
    
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
        
    def test_room_and_furniture(self):
        """Test room and furniture relationships."""
        # Create a room
        room = Room(
            name="Master Bedroom",
            room_type="bedroom",
            property_id=self.property.id,
            square_feet=250
        )
        db.session.add(room)
        db.session.commit()
        
        # Create furniture for the room
        furniture = RoomFurniture(
            name="King Bed",
            furniture_type="bed",
            description="Memory foam mattress",
            room_id=room.id
        )
        db.session.add(furniture)
        db.session.commit()
        
        # Test relationships
        self.assertIn(room, self.property.rooms)
        self.assertIn(furniture, room.room_furniture)
        
        # Test furniture fields
        self.assertEqual(furniture.name, "King Bed")
        self.assertEqual(furniture.furniture_type, "bed")
        self.assertEqual(furniture.description, "Memory foam mattress")
        
        # Test room fields
        self.assertEqual(room.name, "Master Bedroom")
        self.assertEqual(room.room_type, "bedroom")
        self.assertEqual(room.property_id, self.property.id)


if __name__ == '__main__':
    unittest.main() 