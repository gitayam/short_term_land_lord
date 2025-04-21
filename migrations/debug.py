from app import app, db
from app.models import PropertyCalendar, Room

with app.app_context():
    print("Checking PropertyCalendar entries:")
    try:
        calendars = PropertyCalendar.query.all()
        print(f"Found {len(calendars)} calendars")
        for cal in calendars:
            print(f"Calendar ID: {cal.id}, Name: {cal.name}, URL: {cal.ical_url}, Status: {cal.sync_status}")
    except Exception as e:
        print(f"Error querying PropertyCalendar: {e}")

    print("\nChecking Room entries:")
    try:
        rooms = Room.query.all()
        print(f"Found {len(rooms)} rooms")
        for room in rooms:
            print(f"Room ID: {room.id}, Name: {room.name}, Type: {room.room_type}, Property ID: {room.property_id}")
    except Exception as e:
        print(f"Error querying Room: {e}")

    print("\nChecking if room_form_template route exists:")
    try:
        from app.property.routes import room_form_template
        print("room_form_template route exists")
    except Exception as e:
        print(f"Error importing room_form_template: {e}")