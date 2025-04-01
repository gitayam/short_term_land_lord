from flask import render_template, current_app, flash, abort
from flask_login import login_required, current_user
from app.main import bp
from app.models import Property, PropertyCalendar, UserRoles
from datetime import datetime, timedelta
import requests
from icalendar import Calendar
import json

@bp.route('/')
@bp.route('/index')
def index():
    return render_template('main/index.html', title='Home')

@bp.route('/dashboard')
@login_required
def dashboard():
    # Get properties that are visible to the current user
    if current_user.is_property_owner():
        # Property owners see only their properties
        properties = Property.query.filter_by(owner_id=current_user.id).all()
    elif current_user.is_cleaner() or current_user.is_maintenance() or current_user.is_admin():
        # Cleaners, maintenance staff, and admins see all properties
        properties = Property.query.all()
    else:
        properties = []
    
    return render_template('main/dashboard.html', title='Dashboard', properties=properties)

@bp.route('/combined-calendar')
@login_required
def combined_calendar():
    # Get properties that are visible to the current user
    if current_user.is_property_owner():
        # Property owners see only their properties
        properties = Property.query.filter_by(owner_id=current_user.id).all()
    elif current_user.is_cleaner() or current_user.is_maintenance() or current_user.is_admin():
        # Cleaners, maintenance staff, and admins see all properties
        properties = Property.query.all()
    else:
        properties = []
    
    if not properties:
        flash('No properties found.', 'warning')
        return render_template('main/combined_calendar.html', title='Combined Calendar', properties=[], events=[])
    
    # Get all calendars for all properties
    all_calendars = []
    for property in properties:
        calendars = PropertyCalendar.query.filter_by(property_id=property.id).all()
        for calendar in calendars:
            all_calendars.append((property, calendar))
    
    # If no calendars found, still show the page but with message
    if not all_calendars:
        flash('No calendars have been added to any properties. Add a calendar to see bookings.', 'info')
        return render_template('main/combined_calendar.html', title='Combined Calendar', properties=properties, events=[])
    
    # Prepare events data for the calendar
    events = []
    success = False
    property_colors = {}
    color_index = 0
    
    # Define a list of distinct colors for properties
    colors = [
        '#FF5A5F', '#00A699', '#FC642D', '#484848', '#767676',
        '#3D67FF', '#39D5FF', '#BD10E0', '#9013FE', '#50E3C2',
        '#FFB400', '#FF5E3A', '#FF2D55', '#5AC8FA', '#007AFF'
    ]
    
    for property, calendar in all_calendars:
        try:
            # Assign a color to this property if it doesn't have one yet
            if property.id not in property_colors:
                property_colors[property.id] = colors[color_index % len(colors)]
                color_index += 1
            
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
                    
                    # Extract events
                    for component in cal.walk():
                        if component.name == "VEVENT":
                            try:
                                # Get event details with extensive error checking
                                summary = ''
                                start_date = None
                                end_date = None
                                
                                # Try to get summary safely
                                if hasattr(component, 'get') and callable(component.get):
                                    summary_value = component.get('summary')
                                    if summary_value:
                                        summary = str(summary_value)
                                    else:
                                        summary = 'Booking'
                                else:
                                    summary = 'Booking'
                                
                                # Try to get start date safely
                                dtstart = component.get('dtstart')
                                if dtstart and hasattr(dtstart, 'dt'):
                                    start_date = dtstart.dt
                                else:
                                    # Skip this event if no start date
                                    continue
                                
                                # Try to get end date safely
                                dtend = component.get('dtend')
                                if dtend and hasattr(dtend, 'dt'):
                                    end_date = dtend.dt
                                else:
                                    # If no end date, use start date + 1 day
                                    if isinstance(start_date, datetime):
                                        end_date = start_date + timedelta(days=1)
                                    else:
                                        end_date = start_date + timedelta(days=1)
                                
                                # Convert datetime objects to date if necessary
                                if isinstance(start_date, datetime):
                                    start_date = start_date.date()
                                if isinstance(end_date, datetime):
                                    end_date = end_date.date()
                                
                                # Make sure both dates are valid
                                if not (start_date and end_date):
                                    continue
                                
                                # Add event to the list
                                event = {
                                    'title': f"{property.name}: {summary}",
                                    'start': start_date.isoformat(),
                                    'end': end_date.isoformat(),
                                    'backgroundColor': property_colors[property.id],
                                    'borderColor': property_colors[property.id],
                                    'extendedProps': {
                                        'property_name': property.name,
                                        'property_id': property.id,
                                        'service': calendar.get_service_display(),
                                        'room': None if calendar.is_entire_property else calendar.room_name
                                    }
                                }
                                events.append(event)
                                success = True
                            except Exception as e:
                                # Just skip this event if there's a problem with it
                                current_app.logger.error(f"Error parsing event in calendar {calendar.id}: {str(e)}")
                                continue
                    
                    # Update last_synced and status
                    calendar.last_synced = datetime.utcnow()
                    calendar.sync_status = 'Success'
                    calendar.sync_error = None
                    
                except Exception as e:
                    # Problem parsing the iCal data
                    calendar.sync_status = 'Failed'
                    calendar.sync_error = f"Error parsing iCal data: {str(e)[:255]}"
                    flash(f'Error parsing calendar {calendar.name}: {str(e)}', 'warning')
            else:
                # Update sync status
                calendar.sync_status = 'Error'
                calendar.sync_error = f"HTTP error: {response.status_code}"
                flash(f'Could not fetch calendar {calendar.name} (HTTP error {response.status_code})', 'warning')
        except Exception as e:
            # Any other error
            calendar.sync_status = 'Failed'
            calendar.sync_error = str(e)[:255]
            flash(f'Error syncing calendar {calendar.name}: {str(e)}', 'warning')
    
    # If we couldn't fetch any valid events, inform the user
    if not success and all_calendars:
        flash('Could not fetch calendar data from any of the configured sources. Please check your calendar URLs and try again.', 'warning')
    
    # Create legend data using the property colors
    legend_data = []
    for property in properties:
        if property.id in property_colors:
            legend_data.append({
                'name': property.name,
                'color': property_colors[property.id],
                'id': property.id
            })
    
    return render_template('main/combined_calendar.html', 
                          title='Combined Calendar', 
                          properties=properties, 
                          events=events,
                          legend_data=legend_data)
