from flask import Blueprint, render_template, jsonify, request, current_app
from flask_login import login_required, current_user
from app.models import Property, PropertyCalendar, Task
from app import db
from datetime import datetime, timedelta

bp = Blueprint('calendar', __name__, url_prefix='/calendar')

@bp.route('/property/<int:property_id>')
@login_required
def property_calendar(property_id):
    """View property calendar"""
    property = Property.query.get_or_404(property_id)
    
    # Check if user has permission to view this property
    if not (current_user.is_admin or property.owner_id == current_user.id or 
            current_user.is_property_manager or current_user.is_service_staff):
        return "Unauthorized", 403
    
    return render_template('calendar/property_calendar.html', 
                         property=property,
                         title=f'Calendar - {property.name}')

@bp.route('/availability')
@login_required
def availability_calendar():
    """View availability calendar for all properties"""
    if not (current_user.is_admin or current_user.is_property_owner or 
            current_user.is_property_manager):
        return "Unauthorized", 403
    
    # Check for mock data flag
    use_mock = request.args.get('mock', '').lower() == 'true'
    
    if use_mock:
        return render_template('calendar/availability_calendar.html',
                            mock_data=True,
                            title='Property Availability Calendar')
    
    # Get properties the user has access to
    if current_user.is_admin or current_user.is_property_manager:
        properties = Property.query.all()
    else:
        properties = current_user.managed_properties
    
    return render_template('calendar/availability_calendar.html',
                         properties=properties,
                         mock_data=False,
                         title='Property Availability Calendar')

@bp.route('/api/property/<int:property_id>/tasks')
@login_required
def property_tasks_api(property_id):
    """API endpoint for property tasks"""
    # Verify property exists and user has access
    property = Property.query.get_or_404(property_id)
    if not (current_user.is_admin or property.owner_id == current_user.id or 
            current_user.is_property_manager or current_user.is_service_staff):
        return jsonify({"error": "Unauthorized"}), 403
    
    # Get tasks for the property
    tasks = Task.query.filter_by(property_id=property_id).all()
    
    # Format tasks for FullCalendar
    events = []
    for task in tasks:
        events.append({
            'id': task.id,
            'title': task.title,
            'start': task.due_date.isoformat() if task.due_date else None,
            'end': (task.due_date + timedelta(hours=1)).isoformat() if task.due_date else None,
            'url': f'/tasks/{task.id}',
            'className': f'event-{task.status.value.lower()}' if task.status else ''
        })
    
    return jsonify(events)
