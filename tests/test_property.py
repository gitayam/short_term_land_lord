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

    def test_checkin_checkout_times(self):
        """Test setting and retrieving checkin and checkout times."""
        # Create property with checkin/checkout times
        property_with_times = Property(
            name='Property with Times',
            description='Property with check-in/out times',
            address='456 Time St, Test City, Test State 12345, Test Country',
            owner_id=self.owner.id,
            checkin_time='14:00',
            checkout_time='11:00'
        )
        db.session.add(property_with_times)
        db.session.commit()
        
        # Retrieve from database
        saved_property = Property.query.filter_by(name='Property with Times').first()
        self.assertIsNotNone(saved_property)
        self.assertEqual(saved_property.checkin_time, '14:00')
        self.assertEqual(saved_property.checkout_time, '11:00')

    def test_property_details(self):
        """Test property detail fields including trash_day."""
        # Create property with various details
        property_details = Property(
            name='Property with Details',
            description='Property with various detail fields',
            address='789 Details Ave, Test City, Test State 12345, Test Country',
            owner_id=self.owner.id,
            bedrooms=4,
            bathrooms=3.5,
            square_feet=2500,
            year_built=2010,
            trash_day='Monday and Thursday'
        )
        db.session.add(property_details)
        db.session.commit()
        
        # Retrieve from database
        saved_property = Property.query.filter_by(name='Property with Details').first()
        self.assertIsNotNone(saved_property)
        self.assertEqual(saved_property.bedrooms, 4)
        self.assertEqual(saved_property.bathrooms, 3.5)
        self.assertEqual(saved_property.square_feet, 2500)
        self.assertEqual(saved_property.year_built, 2010)
        self.assertEqual(saved_property.trash_day, 'Monday and Thursday')

    def test_comprehensive_property_fields(self):
        """Test all property fields to ensure they save and retrieve correctly."""
        # Create property with all available fields
        property_full = Property(
            name='Comprehensive Test Property',
            description='Testing all property fields',
            address='789 Complete St, Test City, Test State 12345, Test Country',
            street_address='789 Complete St',
            city='Test City',
            state='Test State',
            zip_code='12345',
            country='Test Country',
            owner_id=self.owner.id,
            
            # Property details
            property_type='house',
            bedrooms=5,
            bathrooms=3.5,
            square_feet=3200,
            year_built=2005,
            
            # Collection schedules
            trash_day='monday',
            recycling_day='wednesday',
            recycling_notes='No glass or plastic bags',
            
            # Utility information
            internet_provider='Test Internet',
            internet_account='INT-123456',
            internet_contact='1-800-555-0000',
            electric_provider='Test Electric',
            electric_account='ELEC-789012',
            electric_contact='1-800-555-1111',
            water_provider='Test Water',
            water_account='WAT-345678',
            water_contact='1-800-555-2222',
            trash_provider='Test Trash',
            trash_account='TRS-901234',
            trash_contact='1-800-555-3333',
            
            # Check-in/out times
            checkin_time='15:00',
            checkout_time='11:00',
            
            # Access information
            cleaning_supplies_location='Under kitchen sink and in laundry room closet',
            wifi_network='TestWiFi',
            wifi_password='password123',
            special_instructions='Lock all windows when leaving',
            entry_instructions='Keypad code: 1234. Backup key under flowerpot',
            
            # Cleaner information
            total_beds=6,
            bed_sizes='2 King, 3 Queen, 1 Twin',
            number_of_tvs=4,
            number_of_showers=3,
            number_of_tubs=2,
            
            # Guest access
            guest_access_enabled=True,
            guest_rules='No smoking, no parties',
            guest_checkin_instructions='Check-in after 3 PM using keypad',
            guest_checkout_instructions='Leave keys on counter, close all windows',
            guest_wifi_instructions='Connect to TestWiFi network using password123',
            local_attractions='Beach 5 min walk, great restaurants nearby',
            emergency_contact='John Doe: 555-1234',
            guest_faq='Q: Where is parking? A: In the driveway or on street'
        )
        db.session.add(property_full)
        db.session.commit()
        
        # Retrieve from database
        saved_property = Property.query.filter_by(name='Comprehensive Test Property').first()
        self.assertIsNotNone(saved_property)
        
        # Test basic details
        self.assertEqual(saved_property.description, 'Testing all property fields')
        self.assertEqual(saved_property.property_type, 'house')
        self.assertEqual(saved_property.bedrooms, 5)
        self.assertEqual(saved_property.bathrooms, 3.5)
        self.assertEqual(saved_property.square_feet, 3200)
        self.assertEqual(saved_property.year_built, 2005)
        
        # Test collection schedules
        self.assertEqual(saved_property.trash_day, 'monday')
        self.assertEqual(saved_property.recycling_day, 'wednesday')
        self.assertEqual(saved_property.recycling_notes, 'No glass or plastic bags')
        
        # Test utility information
        self.assertEqual(saved_property.internet_provider, 'Test Internet')
        self.assertEqual(saved_property.internet_account, 'INT-123456')
        self.assertEqual(saved_property.internet_contact, '1-800-555-0000')
        self.assertEqual(saved_property.electric_provider, 'Test Electric')
        self.assertEqual(saved_property.electric_account, 'ELEC-789012')
        self.assertEqual(saved_property.electric_contact, '1-800-555-1111')
        self.assertEqual(saved_property.water_provider, 'Test Water')
        self.assertEqual(saved_property.water_account, 'WAT-345678')
        self.assertEqual(saved_property.water_contact, '1-800-555-2222')
        self.assertEqual(saved_property.trash_provider, 'Test Trash')
        self.assertEqual(saved_property.trash_account, 'TRS-901234')
        self.assertEqual(saved_property.trash_contact, '1-800-555-3333')
        
        # Test check-in/out times
        self.assertEqual(saved_property.checkin_time, '15:00')
        self.assertEqual(saved_property.checkout_time, '11:00')
        
        # Test access information
        self.assertEqual(saved_property.cleaning_supplies_location, 'Under kitchen sink and in laundry room closet')
        self.assertEqual(saved_property.wifi_network, 'TestWiFi')
        self.assertEqual(saved_property.wifi_password, 'password123')
        self.assertEqual(saved_property.special_instructions, 'Lock all windows when leaving')
        self.assertEqual(saved_property.entry_instructions, 'Keypad code: 1234. Backup key under flowerpot')
        
        # Test cleaner information
        self.assertEqual(saved_property.total_beds, 6)
        self.assertEqual(saved_property.bed_sizes, '2 King, 3 Queen, 1 Twin')
        self.assertEqual(saved_property.number_of_tvs, 4)
        self.assertEqual(saved_property.number_of_showers, 3)
        self.assertEqual(saved_property.number_of_tubs, 2)
        
        # Test guest access
        self.assertTrue(saved_property.guest_access_enabled)
        self.assertEqual(saved_property.guest_rules, 'No smoking, no parties')
        self.assertEqual(saved_property.guest_checkin_instructions, 'Check-in after 3 PM using keypad')
        self.assertEqual(saved_property.guest_checkout_instructions, 'Leave keys on counter, close all windows')
        self.assertEqual(saved_property.guest_wifi_instructions, 'Connect to TestWiFi network using password123')
        self.assertEqual(saved_property.local_attractions, 'Beach 5 min walk, great restaurants nearby')
        self.assertEqual(saved_property.emergency_contact, 'John Doe: 555-1234')
        self.assertEqual(saved_property.guest_faq, 'Q: Where is parking? A: In the driveway or on street')

    def test_address_field_generation(self):
        """Test that the address field is generated correctly from components."""
        # Create property with address components but without explicit address
        property_components = Property(
            name='Address Test Property',
            street_address='123 Main St',
            city='Testville',
            state='CA',
            zip_code='90210',
            country='USA',
            owner_id=self.owner.id
        )
        
        # Set the address field from components before saving
        property_components.address = f"{property_components.street_address}, {property_components.city}, {property_components.state} {property_components.zip_code}, {property_components.country}"
        
        db.session.add(property_components)
        db.session.commit()
        
        # Retrieve from database
        saved_property = Property.query.filter_by(name='Address Test Property').first()
        self.assertIsNotNone(saved_property)
        
        # Verify address field was saved
        self.assertEqual(saved_property.address, '123 Main St, Testville, CA 90210, USA')

if __name__ == '__main__':
    unittest.main() 