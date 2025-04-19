import unittest
from datetime import datetime, timedelta
from app import create_app, db
from app.models import User, UserRoles, Property, Room, RoomFurniture
from config import TestConfig

class TestPropertyModel(unittest.TestCase):
    def setUp(self):
        """Set up test environment."""
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        
        # Create a test owner
        self.owner = User(
            first_name='Test',
            last_name='Owner',
            email='owner@example.com',
            role=UserRoles.PROPERTY_OWNER.value
        )
        self.owner.set_password('password')
        
        # Create a test service staff
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
            address='123 Test St, Test City, Test State 12345, Test Country',
            street_address='123 Test St',
            city='Test City',
            state='Test State',
            zip_code='12345',
            country='Test Country',
            owner_id=self.owner.id,
            bedrooms=3,
            bathrooms=2.5,
            square_feet=2000,
            property_type='house'
        )
        db.session.add(self.property)
        db.session.commit()
    
    def tearDown(self):
        """Clean up after tests."""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def test_property_creation(self):
        """Test property creation and database persistence."""
        # Check that property exists in database
        property_in_db = Property.query.filter_by(name='Test Property').first()
        self.assertIsNotNone(property_in_db)
        self.assertEqual(property_in_db.name, 'Test Property')
        self.assertEqual(property_in_db.description, 'A test property')
        self.assertEqual(property_in_db.bedrooms, 3)
        self.assertEqual(property_in_db.bathrooms, 2.5)
        self.assertEqual(property_in_db.square_feet, 2000)
        self.assertEqual(property_in_db.property_type, 'house')
        self.assertEqual(property_in_db.owner_id, self.owner.id)
    
    def test_get_full_address(self):
        """Test getting the full address from components."""
        expected_address = '123 Test St, Test City, Test State 12345, Test Country'
        self.assertEqual(self.property.get_full_address(), expected_address)
        
        # Test with missing components but providing address since it's required
        property_partial = Property(
            name='Partial Address',
            description='Property with partial address',
            address='123 Main St, Some City', # Required field
            street_address='123 Main St',
            city='Some City',
            owner_id=self.owner.id
        )
        db.session.add(property_partial)
        db.session.commit()
        
        # Test address components are correctly combined
        self.assertEqual(property_partial.get_full_address(), '123 Main St, Some City')
    
    def test_guest_access_token(self):
        """Test generating and validating guest access tokens."""
        # Initially no token
        self.assertIsNone(self.property.guest_access_token)
        
        # Generate a token
        token = self.property.generate_guest_access_token()
        self.assertIsNotNone(token)
        self.assertEqual(token, self.property.guest_access_token)
        self.assertGreaterEqual(len(token), 32)
        
        # Check token persistence
        db.session.commit()
        refreshed_property = db.session.get(Property, self.property.id)
        self.assertEqual(refreshed_property.guest_access_token, token)
    
    def test_room_relationships(self):
        """Test room and property relationships."""
        # Create rooms for the property
        master_bedroom = Room(
            name='Master Bedroom',
            description='Large bedroom with ensuite',
            room_type='bedroom',
            property_id=self.property.id
        )
        
        guest_bedroom = Room(
            name='Guest Bedroom',
            description='Smaller bedroom for guests',
            room_type='bedroom',
            property_id=self.property.id
        )
        
        living_room = Room(
            name='Living Room',
            description='Main living area',
            room_type='living',
            property_id=self.property.id
        )
        
        db.session.add_all([master_bedroom, guest_bedroom, living_room])
        db.session.commit()
        
        # Test property to rooms relationship
        rooms = self.property.rooms
        self.assertEqual(len(rooms), 3)
        room_names = [room.name for room in rooms]
        self.assertIn('Master Bedroom', room_names)
        self.assertIn('Guest Bedroom', room_names)
        self.assertIn('Living Room', room_names)
        
        # Test room to property relationship
        self.assertEqual(master_bedroom.property.id, self.property.id)
        self.assertEqual(guest_bedroom.property.id, self.property.id)
        self.assertEqual(living_room.property.id, self.property.id)
    
    def test_furniture_relationships(self):
        """Test room furniture relationships."""
        # Create a room
        bedroom = Room(
            name='Test Bedroom',
            description='A bedroom for testing',
            room_type='bedroom',
            property_id=self.property.id
        )
        db.session.add(bedroom)
        db.session.commit()
        
        # Add furniture to the room
        bed = RoomFurniture(
            name='King Bed',
            description='Memory foam mattress',
            furniture_type='bed',
            room_id=bedroom.id
        )
        
        dresser = RoomFurniture(
            name='Dresser',
            description='Wooden dresser with mirror',
            furniture_type='storage',
            room_id=bedroom.id
        )
        
        db.session.add_all([bed, dresser])
        db.session.commit()
        
        # Test room to furniture relationship
        furniture = bedroom.room_furniture
        self.assertEqual(len(furniture), 2)
        furniture_names = [f.name for f in furniture]
        self.assertIn('King Bed', furniture_names)
        self.assertIn('Dresser', furniture_names)
        
        # Test furniture attributes
        self.assertEqual(bed.room_id, bedroom.id)
        self.assertEqual(bed.furniture_type, 'bed')
        self.assertEqual(dresser.furniture_type, 'storage')
    
    def test_cascade_delete(self):
        """Test manual removal of rooms and furniture when property is deleted."""
        # Create room and furniture
        room = Room(
            name='Delete Test Room',
            room_type='bedroom',
            property_id=self.property.id
        )
        db.session.add(room)
        db.session.commit()
        
        furniture = RoomFurniture(
            name='Delete Test Furniture',
            furniture_type='bed',
            room_id=room.id
        )
        db.session.add(furniture)
        db.session.commit()
        
        # Verify they exist
        self.assertIsNotNone(Room.query.filter_by(name='Delete Test Room').first())
        self.assertIsNotNone(RoomFurniture.query.filter_by(name='Delete Test Furniture').first())
        
        # First delete the furniture (to maintain referential integrity)
        db.session.delete(furniture)
        
        # Then delete the room
        db.session.delete(room)
        
        # Finally delete the property
        property_id = self.property.id
        db.session.delete(self.property)
        db.session.commit()
        
        # Verify everything is gone
        self.assertIsNone(db.session.get(Property, property_id))
        self.assertIsNone(Room.query.filter_by(name='Delete Test Room').first())
        self.assertIsNone(RoomFurniture.query.filter_by(name='Delete Test Furniture').first())

if __name__ == '__main__':
    unittest.main() 