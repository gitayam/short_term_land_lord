from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models import Property, PropertyCalendar, Task, TaskAssignment, TaskProperty, TaskStatus
from app.calendar.forms import CalendarImportForm
from sqlalchemy.orm import aliased
from datetime import datetime, timedelta, date
import json
import icalendar
import recurring_ical_events
import requests
from io import StringIO
import random

bp = Blueprint('calendar', __name__)

@bp.route('/property/<int:property_id>', methods=['GET'])
@login_required
def property_calendar(property_id):
    """View calendar for a specific property"""
    property = Property.query.get_or_404(property_id)
    
    # Check if user has access to this property
    if not property.is_visible_to(current_user):
        flash('You do not have permission to view this calendar.', 'danger')
        return redirect(url_for('property.index'))
    
    # Get tasks for this property
    # Use aliases to avoid duplicate table name errors
    task_property_alias = aliased(TaskProperty)
    
    # Build the base query with proper aliasing
    query = Task.query.join(
        task_property_alias, Task.id == task_property_alias.task_id
    ).filter(
        task_property_alias.property_id == property_id
    )
    
    # If the user is service staff, only show tasks assigned to them
    if current_user.is_service_staff():
        task_assignment_alias = aliased(TaskAssignment)
        query = query.join(
            task_assignment_alias, Task.id == task_assignment_alias.task_id
        ).filter(
            task_assignment_alias.user_id == current_user.id
        )
    
    # Date filters if provided
    start_date = request.args.get('start')
    end_date = request.args.get('end')
    
    if start_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(Task.due_date >= start_date)
        except ValueError:
            pass
            
    if end_date:
        try:
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
            end_date = end_date.replace(hour=23, minute=59, second=59)
            query = query.filter(Task.due_date <= end_date)
        except ValueError:
            pass
    
    # Get final task list
    tasks = query.order_by(Task.due_date.asc()).all()
    
    return render_template('calendar/property.html',
                          title=f'Calendar - {property.name}',
                          property=property,
                          tasks=tasks)

@bp.route('/api/property/<int:property_id>/tasks', methods=['GET'])
@login_required
def property_tasks_api(property_id):
    """API endpoint for tasks as calendar events"""
    property = Property.query.get_or_404(property_id)
    
    # Check if user has access to this property
    if not property.is_visible_to(current_user):
        return jsonify({'error': 'Permission denied'}), 403
    
    # Use aliases to avoid duplicate table name errors
    task_property_alias = aliased(TaskProperty)
    
    # Build the base query with proper aliasing
    query = Task.query.join(
        task_property_alias, Task.id == task_property_alias.task_id
    ).filter(
        task_property_alias.property_id == property_id
    )
    
    # If the user is service staff, only show tasks assigned to them
    if current_user.is_service_staff():
        task_assignment_alias = aliased(TaskAssignment)
        query = query.join(
            task_assignment_alias, Task.id == task_assignment_alias.task_id
        ).filter(
            task_assignment_alias.user_id == current_user.id
        )
    
    # Date filters
    start = request.args.get('start')
    end = request.args.get('end')
    
    if start:
        try:
            start_date = datetime.fromisoformat(start.replace('Z', '+00:00'))
            query = query.filter(Task.due_date >= start_date)
        except (ValueError, TypeError):
            pass
            
    if end:
        try:
            end_date = datetime.fromisoformat(end.replace('Z', '+00:00'))
            query = query.filter(Task.due_date <= end_date)
        except (ValueError, TypeError):
            pass
    
    # Get tasks
    tasks = query.all()
    
    # Format for fullcalendar
    events = []
    for task in tasks:
        if task.due_date:
            # Get assignment info
            assigned_to = None
            for assignment in task.assignments:
                if assignment.user:
                    assigned_to = assignment.user.get_full_name()
                elif assignment.external_name:
                    assigned_to = f"{assignment.external_name} (external)"
            
            # Create event
            event = {
                'id': task.id,
                'title': task.title,
                'start': task.due_date.isoformat(),
                'end': (task.due_date + timedelta(hours=1)).isoformat(),
                'url': url_for('tasks.view', id=task.id),
                'backgroundColor': get_task_color(task),
                'borderColor': get_task_color(task),
                'textColor': '#ffffff',
                'extendedProps': {
                    'status': task.status.value,
                    'priority': task.priority.value,
                    'assignedTo': assigned_to
                }
            }
            events.append(event)
    
    return jsonify(events)

def get_task_color(task):
    """Return a color based on task priority and status"""
    if task.status == TaskStatus.COMPLETED:
        return '#28a745'  # Green for completed
    
    # Colors based on priority
    priority_colors = {
        'LOW': '#17a2b8',      # Info/Blue
        'MEDIUM': '#ffc107',   # Warning/Yellow
        'HIGH': '#fd7e14',     # Orange
        'URGENT': '#dc3545'    # Danger/Red
    }
    
    return priority_colors.get(task.priority.value, '#6c757d')

@bp.route('/availability', methods=['GET'])
@login_required
def availability_calendar():
    """View availability calendar for all accessible properties"""
    
    # Get all properties the user has access to
    if current_user.is_admin or current_user.has_admin_role:
        properties = Property.query.all()
    elif current_user.is_property_owner:
        properties = Property.query.filter_by(owner_id=current_user.id).all()
    else:
        # For staff, find properties they have tasks assigned to
        task_assignment_alias = aliased(TaskAssignment)
        task_property_alias = aliased(TaskProperty)
        
        property_ids = db.session.query(task_property_alias.property_id)\
            .join(Task, Task.id == task_property_alias.task_id)\
            .join(task_assignment_alias, Task.id == task_assignment_alias.task_id)\
            .filter(task_assignment_alias.user_id == current_user.id)\
            .distinct().all()
        
        property_ids = [p[0] for p in property_ids]
        properties = Property.query.filter(Property.id.in_(property_ids)).all()
    
    # Get booking data for each property
    bookings_by_property = {}
    start_dates = []
    end_dates = []
    
    # Option to show mock data for testing
    use_mock_data = request.args.get('mock', 'false').lower() == 'true'
    
    for prop in properties:
        bookings = []
        
        # For testing: if mock parameter is set and no real calendars, generate mock data
        if use_mock_data and (not prop.calendars or not any(cal.ical_url for cal in prop.calendars)):
            # Generate some mock bookings for the next 2 months
            today = datetime.now().date()
            
            # Random bookings in next 60 days
            for _ in range(3):  # 3 mock bookings per property
                # Random start date 0-45 days from now
                start_offset = random.randint(0, 45)
                # Random duration 2-7 days
                duration = random.randint(2, 7)
                
                mock_start = today + timedelta(days=start_offset)
                mock_end = mock_start + timedelta(days=duration)
                
                bookings.append({
                    'summary': 'Mock Booking',
                    'start': mock_start,
                    'end': mock_end
                })
                
                start_dates.append(mock_start)
                end_dates.append(mock_end)
        
        # Process each calendar for the property
        for calendar in prop.calendars:
            if calendar.ical_url:
                try:
                    # Fetch and process the calendar
                    response = requests.get(calendar.ical_url)
                    if response.status_code == 200:
                        cal_content = response.text
                        cal = icalendar.Calendar.from_ical(cal_content)
                        
                        # Get a date range for the next 3 months
                        start_date = datetime.now().date()
                        end_date = start_date + timedelta(days=90)
                        
                        # Get the events, handling recurring events
                        events = recurring_ical_events.of(cal).between(start_date, end_date)
                        
                        for event in events:
                            summary = str(event.get('summary', 'Booking'))
                            dtstart = event.get('dtstart').dt
                            dtend = event.get('dtend').dt
                            
                            # Convert datetime to date if necessary
                            if isinstance(dtstart, datetime):
                                dtstart = dtstart.date()
                            if isinstance(dtend, datetime):
                                dtend = dtend.date()
                            
                            bookings.append({
                                'summary': summary,
                                'start': dtstart,
                                'end': dtend
                            })
                            
                            # Track the earliest and latest dates
                            start_dates.append(dtstart)
                            end_dates.append(dtend)
                            
                except Exception as e:
                    flash(f"Error processing calendar for {prop.name}: {str(e)}", "warning")
        
        # Store bookings with string key for property ID to avoid key access issues in template
        bookings_by_property[str(prop.id)] = {
            'name': prop.name,
            'bookings': bookings
        }
    
    # Determine the date range to display
    if start_dates and end_dates:
        start_date = min(start_dates)
        end_date = max(end_dates)
    else:
        # Default to current month plus next month if no bookings
        start_date = date.today().replace(day=1)
        end_date = (start_date + timedelta(days=60)).replace(day=1) - timedelta(days=1)
    
    # Generate a list of dates for the calendar
    calendar_dates = []
    current_date = start_date
    while current_date <= end_date:
        calendar_dates.append(current_date)
        current_date += timedelta(days=1)
    
    return render_template('calendar/availability.html',
                          title='Property Availability Calendar',
                          properties=properties,
                          bookings_by_property=bookings_by_property,
                          calendar_dates=calendar_dates,
                          start_date=start_date,
                          end_date=end_date,
                          use_mock_data=use_mock_data) 