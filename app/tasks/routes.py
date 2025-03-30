from flask import render_template, redirect, url_for, flash, request, current_app, abort
from flask_login import login_required, current_user
from app import db
from app.tasks import bp
from app.tasks.forms import TaskForm, TaskAssignmentForm, TaskFilterForm
from app.models import (Task, TaskAssignment, TaskProperty, Property, User, 
                       TaskStatus, TaskPriority, RecurrencePattern, UserRoles,
                       PropertyCalendar, CleaningSession)
from datetime import datetime, timedelta
from sqlalchemy import or_
from functools import wraps


def cleaner_required(f):
    """Decorator to restrict access to cleaner users only"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_cleaner():
            flash('This feature is only available to cleaners.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function


@bp.route('/')
@login_required
def index():
    # Initialize filter form
    form = TaskFilterForm()
    form.property.query = Property.query
    form.assignee.query = User.query.filter(User.role.in_([UserRoles.CLEANER, UserRoles.MAINTENANCE]))
    
    # Base query - tasks that the current user can see
    query = Task.query
    
    # Property owners see tasks for their properties
    if current_user.is_property_owner():
        # Get all properties owned by the current user
        owned_property_ids = [p.id for p in current_user.properties]
        
        # Find tasks associated with these properties
        query = query.join(TaskProperty).filter(TaskProperty.property_id.in_(owned_property_ids))
    
    # Cleaners and maintenance personnel see tasks assigned to them
    elif current_user.is_cleaner() or current_user.is_maintenance():
        query = query.join(TaskAssignment).filter(TaskAssignment.user_id == current_user.id)
    
    # Apply filters if form is submitted
    if request.args:
        # Filter by status
        status = request.args.get('status')
        if status:
            query = query.filter(Task.status == TaskStatus(status))
            
        # Filter by priority
        priority = request.args.get('priority')
        if priority:
            query = query.filter(Task.priority == TaskPriority(priority))
            
        # Filter by property
        property_id = request.args.get('property')
        if property_id and property_id.isdigit():
            query = query.join(TaskProperty).filter(TaskProperty.property_id == int(property_id))
            
        # Filter by assignee
        assignee_id = request.args.get('assignee')
        if assignee_id and assignee_id.isdigit():
            query = query.join(TaskAssignment).filter(TaskAssignment.user_id == int(assignee_id))
            
        # Filter by due date range
        due_date_from = request.args.get('due_date_from')
        if due_date_from:
            try:
                from_date = datetime.strptime(due_date_from, '%Y-%m-%d')
                query = query.filter(Task.due_date >= from_date)
            except ValueError:
                pass
                
        due_date_to = request.args.get('due_date_to')
        if due_date_to:
            try:
                to_date = datetime.strptime(due_date_to, '%Y-%m-%d')
                to_date = to_date.replace(hour=23, minute=59, second=59)
                query = query.filter(Task.due_date <= to_date)
            except ValueError:
                pass
    
    # Order by due date (most urgent first) and then by priority
    tasks = query.order_by(Task.due_date.asc(), Task.priority.desc()).all()
    
    # Get active cleaning session for current user if they are a cleaner
    active_session = None
    if current_user.is_cleaner():
        active_session = CleaningSession.get_active_session(current_user.id)
    
    return render_template('tasks/index.html', title='Tasks', tasks=tasks, form=form, active_session=active_session)


@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    # Only property owners can create tasks
    if not current_user.is_property_owner():
        flash('Only property owners can create tasks.', 'danger')
        return redirect(url_for('main.index'))
    
    form = TaskForm()
    
    # Set up query for properties owned by the current user
    form.properties.query = Property.query.filter_by(owner_id=current_user.id)
    
    # Set up calendar choices
    calendar_choices = []
    for property in current_user.properties:
        for calendar in property.calendars:
            calendar_choices.append((calendar.id, f"{property.name} - {calendar.name}"))
    
    form.calendar_id.choices = [(-1, 'None')] + calendar_choices
    
    if form.validate_on_submit():
        # Create new task
        task = Task(
            title=form.title.data,
            description=form.description.data,
            due_date=form.due_date.data,
            status=TaskStatus(form.status.data),
            priority=TaskPriority(form.priority.data),
            notes=form.notes.data,
            is_recurring=form.is_recurring.data,
            recurrence_pattern=RecurrencePattern(form.recurrence_pattern.data) if form.is_recurring.data else RecurrencePattern.NONE,
            recurrence_interval=form.recurrence_interval.data if form.is_recurring.data else 1,
            recurrence_end_date=form.recurrence_end_date.data,
            linked_to_checkout=form.linked_to_checkout.data,
            calendar_id=form.calendar_id.data if form.calendar_id.data != -1 else None,
            creator_id=current_user.id
        )
        
        # Add properties to the task
        for property in form.properties.data:
            task_property = TaskProperty(property=property)
            task.properties.append(task_property)
        
        db.session.add(task)
        db.session.commit()
        
        flash('Task created successfully!', 'success')
        return redirect(url_for('tasks.view', id=task.id))
    
    return render_template('tasks/create.html', title='Create Task', form=form)


@bp.route('/<int:id>')
@login_required
def view(id):
    task = Task.query.get_or_404(id)
    
    # Check if user has permission to view this task
    if not can_view_task(task, current_user):
        flash('You do not have permission to view this task.', 'danger')
        return redirect(url_for('tasks.index'))
    
    # Get properties associated with this task
    properties = [tp.property for tp in task.properties]
    
    # Get assignments for this task
    assignments = task.assignments.all()
    
    # Get active cleaning session for current user if they are a cleaner
    active_session = None
    cleaning_history = []
    if current_user.is_cleaner():
        active_session = CleaningSession.get_active_session(current_user.id)
        # Get cleaning history for this task
        cleaning_history = CleaningSession.query.filter_by(
            task_id=task.id
        ).order_by(CleaningSession.start_time.desc()).all()
    
    return render_template('tasks/view.html', title=task.title, task=task, 
                          properties=properties, assignments=assignments,
                          active_session=active_session, cleaning_history=cleaning_history)


@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    task = Task.query.get_or_404(id)
    
    # Check if user has permission to edit this task
    if not can_edit_task(task, current_user):
        flash('You do not have permission to edit this task.', 'danger')
        return redirect(url_for('tasks.index'))
    
    form = TaskForm()
    
    # Set up query for properties owned by the task creator
    form.properties.query = Property.query.filter_by(owner_id=task.creator_id)
    
    # Set up calendar choices
    calendar_choices = []
    for property in Property.query.filter_by(owner_id=task.creator_id):
        for calendar in property.calendars:
            calendar_choices.append((calendar.id, f"{property.name} - {calendar.name}"))
    
    form.calendar_id.choices = [(-1, 'None')] + calendar_choices
    
    if form.validate_on_submit():
        # Update task
        task.title = form.title.data
        task.description = form.description.data
        task.due_date = form.due_date.data
        task.status = TaskStatus(form.status.data)
        task.priority = TaskPriority(form.priority.data)
        task.notes = form.notes.data
        task.is_recurring = form.is_recurring.data
        task.recurrence_pattern = RecurrencePattern(form.recurrence_pattern.data) if form.is_recurring.data else RecurrencePattern.NONE
        task.recurrence_interval = form.recurrence_interval.data if form.is_recurring.data else 1
        task.recurrence_end_date = form.recurrence_end_date.data
        task.linked_to_checkout = form.linked_to_checkout.data
        task.calendar_id = form.calendar_id.data if form.calendar_id.data != -1 else None
        
        # Update properties
        # First, remove all existing property associations
        TaskProperty.query.filter_by(task_id=task.id).delete()
        
        # Then add the new ones
        for property in form.properties.data:
            task_property = TaskProperty(task=task, property=property)
            db.session.add(task_property)
        
        db.session.commit()
        
        flash('Task updated successfully!', 'success')
        return redirect(url_for('tasks.view', id=task.id))
    
    elif request.method == 'GET':
        # Populate form with existing data
        form.title.data = task.title
        form.description.data = task.description
        form.due_date.data = task.due_date
        form.status.data = task.status.value
        form.priority.data = task.priority.value
        form.notes.data = task.notes
        form.is_recurring.data = task.is_recurring
        form.recurrence_pattern.data = task.recurrence_pattern.value
        form.recurrence_interval.data = task.recurrence_interval
        form.recurrence_end_date.data = task.recurrence_end_date
        form.linked_to_checkout.data = task.linked_to_checkout
        form.calendar_id.data = task.calendar_id if task.calendar_id else -1
        
        # Set selected properties
        form.properties.data = [tp.property for tp in task.properties]
    
    return render_template('tasks/edit.html', title=f'Edit Task: {task.title}', form=form, task=task)


@bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    task = Task.query.get_or_404(id)
    
    # Check if user has permission to delete this task
    if not can_delete_task(task, current_user):
        flash('You do not have permission to delete this task.', 'danger')
        return redirect(url_for('tasks.index'))
    
    # Delete the task
    db.session.delete(task)
    db.session.commit()
    
    flash('Task deleted successfully!', 'success')
    return redirect(url_for('tasks.index'))


@bp.route('/<int:id>/assign', methods=['GET', 'POST'])
@login_required
def assign(id):
    task = Task.query.get_or_404(id)
    
    # Check if user has permission to assign this task
    if not can_edit_task(task, current_user):
        flash('You do not have permission to assign this task.', 'danger')
        return redirect(url_for('tasks.index'))
    
    form = TaskAssignmentForm()
    
    # Set up query for users who can be assigned tasks (cleaners and maintenance)
    form.user.query = User.query.filter(User.role.in_([UserRoles.CLEANER, UserRoles.MAINTENANCE]))
    
    if form.validate_on_submit():
        # Create new assignment
        if form.assign_to_user.data:
            # Assign to existing user
            assignment = TaskAssignment(
                task_id=task.id,
                user_id=form.user.data.id
            )
        else:
            # Assign to external person
            assignment = TaskAssignment(
                task_id=task.id,
                external_name=form.external_name.data,
                external_phone=form.external_phone.data
            )
        
        db.session.add(assignment)
        db.session.commit()
        
        flash('Task assigned successfully!', 'success')
        return redirect(url_for('tasks.view', id=task.id))
    
    # Get existing assignments
    assignments = task.assignments.all()
    
    return render_template('tasks/assign.html', title=f'Assign Task: {task.title}', 
                          form=form, task=task, assignments=assignments)


@bp.route('/<int:task_id>/assignment/<int:assignment_id>/remove', methods=['POST'])
@login_required
def remove_assignment(task_id, assignment_id):
    task = Task.query.get_or_404(task_id)
    assignment = TaskAssignment.query.get_or_404(assignment_id)
    
    # Check if assignment belongs to this task
    if assignment.task_id != task.id:
        abort(404)
    
    # Check if user has permission to edit this task
    if not can_edit_task(task, current_user):
        flash('You do not have permission to modify this task.', 'danger')
        return redirect(url_for('tasks.index'))
    
    # Remove the assignment
    db.session.delete(assignment)
    db.session.commit()
    
    flash('Assignment removed successfully!', 'success')
    return redirect(url_for('tasks.view', id=task.id))


@bp.route('/<int:id>/complete', methods=['POST'])
@login_required
def complete(id):
    task = Task.query.get_or_404(id)
    
    # Check if user has permission to complete this task
    if not can_complete_task(task, current_user):
        flash('You do not have permission to complete this task.', 'danger')
        return redirect(url_for('tasks.index'))
    
    # Mark task as completed
    task.mark_completed(current_user.id)
    db.session.commit()
    
    flash('Task marked as completed!', 'success')
    return redirect(url_for('tasks.view', id=task.id))


@bp.route('/<int:id>/start_cleaning', methods=['POST'])
@login_required
@cleaner_required
def start_cleaning(id):
    task = Task.query.get_or_404(id)
    
    # Check if user has permission to view this task
    if not can_view_task(task, current_user):
        flash('You do not have permission to view this task.', 'danger')
        return redirect(url_for('tasks.index'))
    
    # Check if user already has an active cleaning session
    active_session = CleaningSession.get_active_session(current_user.id)
    if active_session:
        flash('You already have an active cleaning session. Please complete it before starting a new one.', 'warning')
        return redirect(url_for('tasks.view', id=active_session.task_id or id))
    
    # Get the property associated with this task
    property = None
    if task.properties:
        property = task.properties[0].property
    
    if not property:
        flash('This task is not associated with any property.', 'danger')
        return redirect(url_for('tasks.view', id=id))
    
    # Create new cleaning session
    session = CleaningSession(
        cleaner_id=current_user.id,
        property_id=property.id,
        task_id=task.id,
        start_time=datetime.utcnow()
    )
    
    # Update task status to in progress
    task.status = TaskStatus.IN_PROGRESS
    
    db.session.add(session)
    db.session.commit()
    
    flash('Cleaning session started!', 'success')
    return redirect(url_for('tasks.view', id=id))


@bp.route('/<int:id>/complete_cleaning', methods=['POST'])
@login_required
@cleaner_required
def complete_cleaning(id):
    task = Task.query.get_or_404(id)
    
    # Check if user has permission to view this task
    if not can_view_task(task, current_user):
        flash('You do not have permission to view this task.', 'danger')
        return redirect(url_for('tasks.index'))
    
    # Get the active cleaning session
    session = CleaningSession.get_active_session(current_user.id)
    
    if not session:
        flash('You do not have an active cleaning session.', 'warning')
        return redirect(url_for('tasks.view', id=id))
    
    # Complete the session
    duration = session.complete()
    
    # Mark task as completed
    task.mark_completed(current_user.id)
    
    db.session.commit()
    
    flash(f'Cleaning completed! Total time: {session.get_duration_display()}', 'success')
    return redirect(url_for('tasks.view', id=id))


@bp.route('/cleaning_history')
@login_required
@cleaner_required
def cleaning_history():
    # Get all cleaning sessions for the current user
    sessions = CleaningSession.query.filter_by(
        cleaner_id=current_user.id
    ).order_by(CleaningSession.start_time.desc()).all()
    
    return render_template('tasks/cleaning_history.html', title='Cleaning History', sessions=sessions)


def can_view_task(task, user):
    """Check if a user can view a task"""
    # Task creator can always view
    if task.creator_id == user.id:
        return True
    
    # Property owners can view tasks for their properties
    if user.is_property_owner():
        # Get all properties owned by the user
        owned_property_ids = [p.id for p in user.properties]
        
        # Check if any task property is owned by the user
        for task_property in task.properties:
            if task_property.property_id in owned_property_ids:
                return True
    
    # Users assigned to the task can view it
    for assignment in task.assignments:
        if assignment.user_id == user.id:
            return True
    
    return False


def can_edit_task(task, user):
    """Check if a user can edit a task"""
    # Only the creator or property owner can edit
    if task.creator_id == user.id:
        return True
    
    # Property owners can edit tasks for their properties
    if user.is_property_owner():
        # Get all properties owned by the user
        owned_property_ids = [p.id for p in user.properties]
        
        # Check if any task property is owned by the user
        for task_property in task.properties:
            if task_property.property_id in owned_property_ids:
                return True
    
    return False


def can_delete_task(task, user):
    """Check if a user can delete a task"""
    # Only the creator can delete
    return task.creator_id == user.id


def can_complete_task(task, user):
    """Check if a user can mark a task as completed"""
    # Creator can complete
    if task.creator_id == user.id:
        return True
    
    # Assigned users can complete
    for assignment in task.assignments:
        if assignment.user_id == user.id:
            return True
    
    return False