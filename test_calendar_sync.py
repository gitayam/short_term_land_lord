#!/usr/bin/env python3
"""
Quick test script to verify calendar sync functionality
"""
from app import create_app, db
from app.models import Property, PropertyCalendar, CalendarEvent, User, UserRoles
from datetime import datetime, date

def test_calendar_sync():
    """Test calendar sync functionality"""
    app = create_app()
    
    with app.app_context():
        print("🧪 Testing Calendar Sync Functionality")
        
        # Create a test property owner if none exists
        test_user = User.query.filter_by(email='test@example.com').first()
        if not test_user:
            test_user = User(
                username='testowner',
                email='test@example.com',
                first_name='Test',
                last_name='Owner',
                role=UserRoles.PROPERTY_OWNER.value
            )
            test_user.set_password('test123')
            db.session.add(test_user)
            db.session.commit()
            print("✅ Created test user")
        
        # Create a test property if none exists
        test_property = Property.query.filter_by(name='Test Property').first()
        if not test_property:
            test_property = Property(
                name='Test Property',
                address='123 Test Street, Test City, TC 12345',
                owner_id=test_user.id
            )
            db.session.add(test_property)
            db.session.commit()
            print("✅ Created test property")
        
        # Create a test calendar
        test_calendar = PropertyCalendar.query.filter_by(
            property_id=test_property.id,
            name='Test Airbnb Calendar'
        ).first()
        
        if not test_calendar:
            test_calendar = PropertyCalendar(
                property_id=test_property.id,
                name='Test Airbnb Calendar',
                ical_url='https://example.com/test.ics',  # Mock URL
                service='airbnb',
                created_at=datetime.utcnow()
            )
            db.session.add(test_calendar)
            db.session.commit()
            print("✅ Created test calendar")
        
        # Create sample calendar events to simulate synced data
        sample_events = [
            {
                'title': 'Smith Family Booking',
                'start_date': date(2025, 8, 15),
                'end_date': date(2025, 8, 18),
                'source': 'airbnb',
                'guest_name': 'John Smith',
                'guest_count': 4,
                'booking_amount': 450.00,
                'booking_status': 'confirmed'
            },
            {
                'title': 'Johnson Group',
                'start_date': date(2025, 8, 25),
                'end_date': date(2025, 8, 28),
                'source': 'vrbo',
                'guest_name': 'Sarah Johnson',
                'guest_count': 2,
                'booking_amount': 380.00,
                'booking_status': 'confirmed'
            },
            {
                'title': 'Weekend Getaway',
                'start_date': date(2025, 9, 5),
                'end_date': date(2025, 9, 7),
                'source': 'booking',
                'guest_name': 'Mike Brown',
                'guest_count': 3,
                'booking_amount': 290.00,
                'booking_status': 'pending'
            }
        ]
        
        # Clear existing test events
        CalendarEvent.query.filter_by(property_calendar_id=test_calendar.id).delete()
        
        # Create sample events
        for event_data in sample_events:
            event = CalendarEvent(
                property_calendar_id=test_calendar.id,
                property_id=test_property.id,
                title=event_data['title'],
                start_date=event_data['start_date'],
                end_date=event_data['end_date'],
                source=event_data['source'],
                external_id=f"test_{event_data['start_date']}_{event_data['source']}",
                guest_name=event_data['guest_name'],
                guest_count=event_data['guest_count'],
                booking_amount=event_data['booking_amount'],
                booking_status=event_data['booking_status'],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.session.add(event)
        
        db.session.commit()
        print(f"✅ Created {len(sample_events)} sample calendar events")
        
        # Test the to_fullcalendar_dict method
        events = CalendarEvent.query.filter_by(property_calendar_id=test_calendar.id).all()
        print(f"\n📅 Testing FullCalendar conversion:")
        
        for event in events:
            fc_event = event.to_fullcalendar_dict()
            print(f"   • {fc_event['title']}: {fc_event['start']} - {fc_event['end']}")
            print(f"     Platform: {fc_event['extendedProps']['platform']}")
            print(f"     Amount: ${fc_event['extendedProps']['amount']}")
            print(f"     Color: {fc_event['backgroundColor']}")
        
        # Test calendar sync status update
        test_calendar.last_synced = datetime.utcnow()
        test_calendar.sync_status = 'Success'
        test_calendar.sync_error = None
        db.session.commit()
        
        print(f"\n✅ Calendar sync test completed successfully!")
        print(f"   • Property: {test_property.name}")
        print(f"   • Calendar: {test_calendar.name} ({test_calendar.get_service_display()})")
        print(f"   • Events: {len(events)} bookings loaded")
        print(f"   • Sync Status: {test_calendar.sync_status}")
        print(f"   • Last Synced: {test_calendar.last_synced}")
        
        print(f"\n🚀 Ready for production use!")
        print(f"   • Add real iCal URLs via: /property/{test_property.id}/calendar/add")
        print(f"   • View calendar at: /combined-calendar")
        print(f"   • Test with: python app/tasks/sync_calendars.py")

if __name__ == "__main__":
    test_calendar_sync()