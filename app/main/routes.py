from flask import render_template, current_app, flash, abort, jsonify
from flask_login import login_required, current_user
from app.main import bp
from app.models import Property, PropertyCalendar, UserRoles, Booking, BookingTask, db
from datetime import datetime, timedelta
import requests
from icalendar import Calendar
import json
from sqlalchemy import or_

@bp.route('/')
@bp.route('/index')
def index():
    return render_template('main/index.html', title='Home')

@bp.route('/dashboard')
@login_required
def dashboard():
    # Get all properties if admin or property manager
    if current_user.has_admin_role or current_user.is_property_manager:
        properties = Property.query.all()
    # Property owners see only their properties
    elif current_user.is_property_owner:
        properties = Property.query.filter_by(owner_id=current_user.id).all()
    # Service staff see properties they have tasks for
    elif current_user.is_service_staff:
        properties = [p for p in Property.query.all() if p.is_visible_to(current_user)]
    else:
        properties = []
    
    return render_template('main/dashboard.html', title='Dashboard', properties=properties)

@bp.route('/combined-calendar')
@login_required
def combined_calendar():
    try:
        # Get all properties if admin or property manager
        if current_user.has_admin_role or current_user.is_property_manager:
            properties = Property.query.order_by(Property.name).all()
        # Property owners see only their properties
        elif current_user.is_property_owner:
            properties = Property.query.filter_by(owner_id=current_user.id).order_by(Property.name).all()
        # Service staff see properties they have tasks for
        elif current_user.is_service_staff:
            properties = [p for p in Property.query.order_by(Property.name).all() if p.is_visible_to(current_user)]
        else:
            properties = []
        
        if not properties:
            flash('No properties found.', 'warning')
            return render_template('main/combined_calendar.html', title='Combined Calendar', properties=[], resources=[], events=[])
        
        # Prepare resources list for FullCalendar
        resources = [{'id': str(prop.id), 'title': prop.name} for prop in properties]
        
        # Get all calendars for all properties
        all_calendars = []
        for property in properties:
            calendars = PropertyCalendar.query.filter_by(property_id=property.id).all()
            for calendar in calendars:
                all_calendars.append((property, calendar))
        
        # If no calendars found, still show the page but with message
        if not all_calendars:
            flash('No calendars have been added to any properties. Add a calendar to see bookings.', 'info')
            return render_template('main/combined_calendar.html', title='Combined Calendar', properties=properties, resources=resources, events=[])
        
        # Sync calendars and store events in database
        for property, calendar in all_calendars:
            try:
                # Log the attempt to fetch
                current_app.logger.info(f"Attempting to fetch calendar {calendar.id}: {calendar.name} - URL: {calendar.ical_url}")
                
                # Fetch the iCal data with timeout to prevent hanging and custom headers
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
                    'Accept': 'text/calendar,application/ics,*/*'
                }
                
                response = requests.get(calendar.ical_url, 
                                    headers=headers, 
                                    timeout=15,
                                    verify=True)
                
                if response.status_code == 200:
                    # Parse the iCal data
                    try:
                        cal = Calendar.from_ical(response.text)
                        
                        # Track processed external IDs to handle deletions
                        processed_external_ids = set()
                        
                        # Extract events
                        for component in cal.walk():
                            if component.name == "VEVENT":
                                try:
                                    # Get event details with extensive error checking
                                    summary = str(component.get('summary', 'Booking'))
                                    
                                    # Get start date
                                    dtstart = component.get('dtstart')
                                    if not (dtstart and hasattr(dtstart, 'dt')):
                                        continue
                                    start_date = dtstart.dt
                                    if isinstance(start_date, datetime):
                                        start_date = start_date.date()
                                    
                                    # Get end date
                                    dtend = component.get('dtend')
                                    if dtend and hasattr(dtend, 'dt'):
                                        end_date = dtend.dt
                                        if isinstance(end_date, datetime):
                                            end_date = end_date.date()
                                    else:
                                        end_date = start_date + timedelta(days=1)
                                    
                                    # Extract guest name from summary
                                    guest_name = None
                                    if ":" in summary:
                                        parts = summary.split(":", 1)
                                        guest_name = parts[1].strip()
                                    elif "-" in summary:
                                        parts = summary.split("-", 1)
                                        guest_name = parts[0].strip()
                                    
                                    # Extract price if available
                                    amount = None
                                    description = str(component.get('description', ''))
                                    import re
                                    price_match = re.search(r'\$(\d+(\.\d+)?)', description)
                                    if price_match:
                                        amount = price_match.group(1)
                                    
                                    # Get external ID (UID)
                                    external_id = str(component.get('uid', ''))
                                    processed_external_ids.add(external_id)
                                    
                                    # Find existing booking or create new one
                                    booking = Booking.query.filter_by(
                                        calendar_id=calendar.id,
                                        external_id=external_id
                                    ).first()
                                    
                                    if not booking:
                                        booking = Booking(
                                            property_id=property.id,
                                            calendar_id=calendar.id,
                                            external_id=external_id
                                        )
                                        db.session.add(booking)
                                    
                                    # Update booking details
                                    booking.title = summary
                                    booking.start_date = start_date
                                    booking.end_date = end_date
                                    booking.guest_name = guest_name
                                    booking.amount = amount
                                    booking.source_url = str(component.get('url', '')) or None
                                    booking.notes = description or None
                                    booking.room_name = calendar.room_name
                                    booking.is_entire_property = calendar.is_entire_property
                                    booking.last_synced = datetime.utcnow()
                                    
                                except Exception as e:
                                    current_app.logger.error(f"Error processing event in calendar {calendar.id}: {str(e)}")
                                    continue
                        
                        # Remove events that no longer exist in the feed
                        old_bookings = Booking.query.filter(
                            Booking.calendar_id == calendar.id,
                            Booking.external_id.notin_(processed_external_ids)
                        ).all()
                        for old_booking in old_bookings:
                            db.session.delete(old_booking)
                        
                        # Update calendar sync status
                        calendar.last_synced = datetime.utcnow()
                        calendar.sync_status = 'Success'
                        calendar.sync_error = None
                        
                        # Commit all changes
                        db.session.commit()
                        
                    except Exception as e:
                        calendar.sync_status = 'Failed'
                        calendar.sync_error = f"Error parsing iCal data: {str(e)[:255]}"
                        current_app.logger.error(f"Error parsing calendar {calendar.id}: {str(e)}")
                        db.session.rollback()
                else:
                    calendar.sync_status = 'Error'
                    calendar.sync_error = f"HTTP error: {response.status_code}"
                    current_app.logger.error(f"HTTP error {response.status_code} fetching calendar {calendar.id}")
            except Exception as e:
                calendar.sync_status = 'Failed'
                calendar.sync_error = str(e)[:255]
                current_app.logger.error(f"Error syncing calendar {calendar.id}: {str(e)}")
                db.session.rollback()
        
        # Get all bookings for display
        property_ids = [p.id for p in properties]
        bookings = Booking.query.filter(
            Booking.property_id.in_(property_ids),
            Booking.end_date >= datetime.now().date()
        ).all()
        
        events = [booking.to_dict() for booking in bookings]
        
        return render_template('main/combined_calendar.html',
                            title='Combined Calendar',
                            properties=properties,
                            resources=resources,
                            events=events)
                            
    except Exception as e:
        current_app.logger.error(f"Error in combined_calendar view: {str(e)}")
        flash('An error occurred while loading the calendar. Please try again later.', 'error')
        return render_template('main/combined_calendar.html',
                            title='Combined Calendar',
                            properties=[],
                            resources=[],
                            events=[])

@bp.route('/dashboard/events')
@login_required
def dashboard_events():
    try:
        # Get properties based on user role
        if current_user.has_admin_role or current_user.is_property_manager:
            properties = Property.query.all()
        elif current_user.is_property_owner:
            properties = Property.query.filter_by(owner_id=current_user.id).all()
        elif current_user.is_service_staff:
            # Get properties where user has tasks
            task_properties = db.session.query(Property).join(Booking).join(BookingTask).filter(
                BookingTask.assigned_to_id == current_user.id
            ).distinct().all()
            properties = [p for p in task_properties if p.is_visible_to(current_user)]
        else:
            properties = []

        if not properties:
            return jsonify([])

        # Get all upcoming bookings for these properties
        property_ids = [p.id for p in properties]
        bookings = Booking.query.filter(
            Booking.property_id.in_(property_ids),
            Booking.end_date >= datetime.now().date()
        ).all()

        events = [booking.to_dict() for booking in bookings]
        return jsonify(events)

    except Exception as e:
        current_app.logger.error(f"Error in dashboard_events: {str(e)}")
        return jsonify([])