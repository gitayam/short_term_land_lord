from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models import Property, PropertyCalendar, Task, TaskAssignment, TaskProperty, TaskStatus
from app.calendar.forms import CalendarImportForm
from sqlalchemy.orm import aliased
from datetime import datetime, timedelta

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