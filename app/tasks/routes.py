from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, abort, jsonify
from flask_login import login_required, current_user
from app import db
from app.tasks import bp
from app.forms.task_forms import (TaskForm, TaskAssignmentForm, TaskFilterForm, VideoUploadForm, 
                           IssueReportForm, CleaningFeedbackForm, RepairRequestForm, ConvertToTaskForm,
                           TaskTemplateForm)
from app.models import (Task, TaskAssignment, TaskProperty, Property, User, 
                       TaskStatus, TaskPriority, RecurrencePattern, UserRoles, ServiceType,
                       PropertyCalendar, CleaningSession, CleaningMedia, MediaType,
                       IssueReport, StorageBackend, CleaningFeedback, InventoryTransaction, TransactionType,
                       RepairRequest, RepairRequestMedia, RepairRequestStatus, RepairRequestSeverity,
                       TaskTemplate)
from app.tasks.media import save_file_to_storage, allowed_file
from app.notifications.service import send_task_assignment_notification, send_repair_request_notification
from datetime import datetime, timedelta
from sqlalchemy import or_
from functools import wraps
import os
import secrets
from werkzeug.utils import secure_filename
import logging


def cleaner_required(f):
    """Decorator to restrict access to users who can perform cleaning tasks"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_service_staff:
            flash('This feature is only available to cleaning staff.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function


# The maintenance_required decorator is no longer needed as we now use service_staff_required


def service_staff_required(f):
    """Decorator to restrict access to service staff users"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_service_staff:
            flash('This feature is only available to service staff.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function


@bp.route('/')
@login_required
def index():
    """Show all tasks"""
    
    # Get current user's role
    user_role = current_user.role
    
    # Get all tasks the user has access to
    if current_user.is_property_owner:
        # For property owners, show all tasks related to their properties
        # and tasks they created (even if not assigned to a property)
        owned_property_ids = [p.id for p in current_user.owned_properties]
        
        # Get tasks related to properties
        property_tasks = db.session.query(Task).join(
            TaskProperty, TaskProperty.task_id == Task.id
        ).filter(
            TaskProperty.property_id.in_(owned_property_ids)
        ).distinct()
        
        # Get tasks created by this user
        created_tasks = Task.query.filter(Task.creator_id == current_user.id)
        
        # Combine both querysets
        tasks = property_tasks.union(created_tasks).all()
    elif current_user.is_service_staff:
        # For service staff, show tasks assigned to them
        tasks = db.session.query(Task).join(
            TaskAssignment, TaskAssignment.task_id == Task.id
        ).filter(
            TaskAssignment.user_id == current_user.id
        ).all()
    else:
        # For other users (like admins), show all tasks
        tasks = Task.query.all()
    
    return render_template('tasks/index.html', 
                          title='Tasks', 
                          tasks=tasks)


@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    form = TaskForm()
    
    # Initialize properties field with a query_factory
    if current_user.is_property_owner:
        form.properties.query_factory = lambda: Property.query.filter_by(owner_id=current_user.id).all()
    elif current_user.is_admin or current_user.is_property_manager:
        form.properties.query_factory = lambda: Property.query.all()
    else:
        form.properties.query_factory = lambda: []
    
    # Set up calendar choices
    calendar_choices = []
    if current_user.is_property_owner:
        for property in current_user.properties:
            for calendar in property.calendars:
                calendar_choices.append((calendar.id, f"{property.name} - {calendar.name}"))
    
    form.calendar_id.choices = [(-1, 'None')] + calendar_choices
    
    # Get suggested task templates
    task_templates = TaskTemplate.query.filter(
        db.or_(
            TaskTemplate.creator_id == current_user.id,
            TaskTemplate.is_global == True
        )
    ).order_by(TaskTemplate.sequence_number.asc()).all()
    
    if form.validate_on_submit():
        try:
            # Create the task without requiring property_id
            task = Task(
                title=form.title.data,
                description=form.description.data,
                due_date=form.due_date.data,
                status=TaskStatus(form.status.data),
                priority=TaskPriority(form.priority.data.lower()) if isinstance(form.priority.data, str) else form.priority.data,
                notes=form.notes.data,
                creator_id=current_user.id,
                property_id=None,  # Explicitly set to None
                assign_to_next_cleaner=form.assign_to_next_cleaner.data
            )
            
            # Handle recurrence if enabled
            if form.is_recurring.data:
                task.is_recurring = True
                task.recurrence_pattern = form.recurrence_pattern.data
                task.recurrence_interval = form.recurrence_interval.data
                task.recurrence_end_date = form.recurrence_end_date.data
            
            # Handle calendar link if enabled
            if form.linked_to_checkout.data and form.calendar_id.data and form.calendar_id.data != -1:
                task.linked_to_checkout = True
                task.calendar_id = form.calendar_id.data
            
            db.session.add(task)
            db.session.commit()
            
            # Now that we have a task ID, associate with properties if any were selected
            if form.properties.data:
                try:
                    for property in form.properties.data:
                        task_property = TaskProperty(
                            task_id=task.id, 
                            property_id=property.id
                        )
                        db.session.add(task_property)
                    
                    db.session.commit()
                except Exception as e:
                    current_app.logger.error(f"Error associating task with properties: {str(e)}")
                    flash('Task was created but there was an error associating it with properties.', 'warning')
            
            flash('Task created successfully!', 'success')
            return redirect(url_for('tasks.view', id=task.id))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating task: {str(e)}")
            flash(f'There was an error creating the task: {str(e)}', 'danger')
    
    return render_template('tasks/create.html', 
                          title='Create Task', 
                          form=form,
                          task_templates=task_templates)


@bp.route('/<int:id>')
@login_required
def view(id):
    task = Task.query.get_or_404(id)
    
    # Check if user has permission to view this task
    if not can_view_task(task, current_user):
        flash('You do not have permission to view this task.', 'danger')
        return redirect(url_for('tasks.index'))
    
    # Get properties associated with this task
    properties = task.properties
    
    # Get assignments for this task
    assignments = task.assignments.all()
    
    # Get active cleaning session for current user if they are a cleaner
    active_session = None
    cleaning_history = []
    if current_user.is_service_staff:
        active_session = CleaningSession.get_active_session(current_user.id)
        # Get cleaning history for this task
        cleaning_history = CleaningSession.query.filter_by(
            task_id=task.id
        ).order_by(CleaningSession.start_time.desc()).all()
    elif current_user.is_property_owner:
        # Property owners also see cleaning history
        cleaning_history = CleaningSession.query.filter_by(
            task_id=task.id
        ).order_by(CleaningSession.start_time.desc()).all()
    
    return render_template('tasks/view.html', title=task.title, task=task, 
                          properties=properties, assignments=assignments,
                          active_session=active_session, cleaning_history=cleaning_history,
                          MediaType=MediaType)


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
        try:
            # Update task
            task.title = form.title.data
            task.description = form.description.data
            task.due_date = form.due_date.data
            task.status = TaskStatus(form.status.data)
            task.priority = TaskPriority(form.priority.data.lower()) if isinstance(form.priority.data, str) else form.priority.data
            task.notes = form.notes.data
            task.is_recurring = form.is_recurring.data
            task.recurrence_pattern = RecurrencePattern(form.recurrence_pattern.data) if form.is_recurring.data else RecurrencePattern.NONE
            task.recurrence_interval = form.recurrence_interval.data if form.is_recurring.data else 1
            task.recurrence_end_date = form.recurrence_end_date.data
            task.linked_to_checkout = form.linked_to_checkout.data
            task.calendar_id = form.calendar_id.data if form.calendar_id.data != -1 else None
            task.assign_to_next_cleaner = form.assign_to_next_cleaner.data
            # Make sure property_id is null if no direct property is assigned
            task.property_id = None
            
            # First save the task changes
            db.session.commit()
            
            # Update properties - handling separately to avoid null property_id issues
            # First, remove all existing property associations
            TaskProperty.query.filter_by(task_id=task.id).delete()
            
            # Then add the new ones
            if form.properties.data:
                for property in form.properties.data:
                    task_property = TaskProperty(
                        task_id=task.id, 
                        property_id=property.id
                    )
                    db.session.add(task_property)
                
                db.session.commit()
            
            flash('Task updated successfully!', 'success')
            return redirect(url_for('tasks.view', id=task.id))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating task: {str(e)}")
            flash(f'There was an error updating the task: {str(e)}', 'danger')
    elif request.method == 'GET':
        # Fill form with current task data
        form.title.data = task.title
        form.description.data = task.description
        form.due_date.data = task.due_date
        form.status.data = task.status.value if hasattr(task.status, 'value') else task.status
        form.priority.data = task.priority.value if hasattr(task.priority, 'value') else task.priority
        form.notes.data = task.notes
        form.is_recurring.data = task.is_recurring
        form.recurrence_pattern.data = task.recurrence_pattern.value if hasattr(task.recurrence_pattern, 'value') else task.recurrence_pattern
        form.recurrence_interval.data = task.recurrence_interval
        form.recurrence_end_date.data = task.recurrence_end_date
        form.assign_to_next_cleaner.data = task.assign_to_next_cleaner
        form.linked_to_checkout.data = task.linked_to_checkout
        form.calendar_id.data = task.calendar_id if task.calendar_id else -1
        
        # Current properties
        form.properties.data = [tp.property for tp in task.task_properties]
    
    return render_template('tasks/edit.html', 
                          title='Edit Task', 
                          form=form,
                          task=task)


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
    
    # Check if there are any service staff users
    service_staff = User.query.filter_by(role=UserRoles.SERVICE_STAFF.value).all()
    has_service_staff = len(service_staff) > 0
    
    # Update the user field query to only show service staff
    form.user.query = User.query.filter(User.role == UserRoles.SERVICE_STAFF.value)
    
    assignments = task.assignments.all()
    
    if form.validate_on_submit():
        if form.assign_to_user.data:
            # Creating assignment for existing user
            task_assignment = TaskAssignment(
                task_id=task.id,
                user_id=form.user.data.id,
                service_type=form.service_type.data
            )
            
            # Send notification to the assignee
            send_task_assignment_notification(task, form.user.data)
        else:
            # Check if a user exists with this email or phone
            external_email = form.external_email.data
            if external_email:
                user = User.query.filter_by(email=external_email).first()
                if user:
                    # User found, create assignment for this user
                    task_assignment = TaskAssignment(
                        task_id=task.id,
                        user_id=user.id,
                        service_type=form.service_type.data
                    )
                    
                    # Send notification to the assignee
                    send_task_assignment_notification(task, user)
                    flash(f'Task assigned to existing user: {user.get_full_name()}', 'success')
                else:
                    # Creating assignment for external person
                    task_assignment = TaskAssignment(
                        task_id=task.id,
                        external_name=form.external_name.data,
                        external_phone=form.external_phone.data,
                        external_email=external_email,
                        service_type=form.service_type.data
                    )
            else:
                # Creating assignment for external person without email
                task_assignment = TaskAssignment(
                    task_id=task.id,
                    external_name=form.external_name.data,
                    external_phone=form.external_phone.data,
                    service_type=form.service_type.data
                )
        
        db.session.add(task_assignment)
        db.session.commit()
        
        flash('Task assigned successfully!', 'success')
        return redirect(url_for('tasks.view', id=task.id))
    
    return render_template('tasks/assign.html', 
                          title='Assign Task', 
                          task=task, 
                          form=form, 
                          assignments=assignments,
                          has_service_staff=has_service_staff)


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


def assign_tasks_to_next_cleaner(property_id, cleaner_id):
    """
    Assign all tasks marked for 'next cleaner' to the specified cleaner
    for the given property.
    """
    # Find all tasks for this property that are marked for next cleaner assignment
    tasks = Task.query.join(TaskProperty).filter(
        TaskProperty.property_id == property_id,
        Task.assign_to_next_cleaner == True,
        Task.status != TaskStatus.COMPLETED
    ).all()
    
    # Assign each task to the cleaner
    for task in tasks:
        # Check if the task is already assigned to this cleaner
        existing_assignment = TaskAssignment.query.filter_by(
            task_id=task.id,
            user_id=cleaner_id
        ).first()
        
        if not existing_assignment:
            # Create a new assignment
            assignment = TaskAssignment(
                task_id=task.id,
                user_id=cleaner_id,
                service_type=ServiceType.CLEANING  # Default to cleaning service type
            )
            db.session.add(assignment)
            
            # Send notification to the assigned user
            cleaner = User.query.get(cleaner_id)
            if cleaner:
                send_task_assignment_notification(task, cleaner)
    
    db.session.commit()
    return len(tasks)


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
    
    # Assign any tasks marked for "next cleaner" to this cleaner
    assigned_count = assign_tasks_to_next_cleaner(property.id, current_user.id)
    if assigned_count > 0:
        flash(f'{assigned_count} additional tasks have been assigned to you as the current cleaner.', 'info')
    
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
    
    # Check if start and end videos are required
    require_videos = current_app.config.get('REQUIRE_CLEANING_VIDEOS', False)
    
    if require_videos:
        # Check if start video exists
        if not session.has_start_video:
            flash('You must upload a start video before completing the cleaning.', 'warning')
            return redirect(url_for('tasks.upload_video', session_id=session.id))
        
        # Check if end video exists
        if not session.has_end_video:
            flash('You must upload an end video before completing the cleaning.', 'warning')
            return redirect(url_for('tasks.upload_video', session_id=session.id))
    
    # Complete the session
    duration = session.complete()
    
    # Mark task as completed
    task.mark_completed(current_user.id)
    
    db.session.commit()
    
    flash(f'Cleaning completed! Total time: {session.get_duration_display()}', 'success')
    
    # Redirect to feedback form
    return redirect(url_for('tasks.feedback', session_id=session.id))


@bp.route('/<int:session_id>/feedback', methods=['GET', 'POST'])
@login_required
@cleaner_required
def feedback(session_id):
    # Get the cleaning session
    session = CleaningSession.query.get_or_404(session_id)
    
    # Check if the current user is the assigned cleaner
    if session.cleaner_id != current_user.id:
        flash('You can only provide feedback for your own cleaning sessions.', 'danger')
        return redirect(url_for('tasks.index'))
    
    # Check if feedback already exists
    existing_feedback = CleaningFeedback.query.filter_by(cleaning_session_id=session_id).first()
    if existing_feedback:
        flash('You have already provided feedback for this cleaning session.', 'info')
        return redirect(url_for('tasks.view', id=session.task_id))
    
    form = CleaningFeedbackForm()
    
    if form.validate_on_submit():
        # Create feedback record
        feedback = CleaningFeedback(
            cleaning_session_id=session_id,
            rating=form.rating.data,
            notes=form.notes.data
        )
        
        db.session.add(feedback)
        db.session.commit()
        
        flash('Thank you for your feedback!', 'success')
        return redirect(url_for('tasks.view', id=session.task_id))
    
    return render_template('tasks/feedback_form.html', 
                          title='Cleaning Feedback', 
                          form=form, 
                          session=session)


@bp.route('/<int:session_id>/submit_feedback', methods=['POST'])
@login_required
@cleaner_required
def submit_feedback(session_id):
    # Get the cleaning session
    session = CleaningSession.query.get_or_404(session_id)
    
    # Check if the current user is the assigned cleaner
    if session.cleaner_id != current_user.id:
        flash('You can only provide feedback for your own cleaning sessions.', 'danger')
        return redirect(url_for('tasks.index'))
    
    # Check if feedback already exists
    existing_feedback = CleaningFeedback.query.filter_by(cleaning_session_id=session_id).first()
    if existing_feedback:
        flash('You have already provided feedback for this cleaning session.', 'info')
        return redirect(url_for('tasks.view', id=session.task_id))
    
    form = CleaningFeedbackForm()
    
    if form.validate_on_submit():
        # Create feedback record
        feedback = CleaningFeedback(
            cleaning_session_id=session_id,
            rating=form.rating.data,
            notes=form.notes.data
        )
        
        db.session.add(feedback)
        db.session.commit()
        
        flash('Thank you for your feedback!', 'success')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{getattr(form, field).label.text}: {error}', 'danger')
    
    return redirect(url_for('tasks.view', id=session.task_id))


@bp.route('/cleaning_history')
@login_required
@cleaner_required
def cleaning_history():
    # Get all cleaning sessions for the current user
    sessions = CleaningSession.query.filter_by(
        cleaner_id=current_user.id
    ).order_by(CleaningSession.start_time.desc()).all()
    
    return render_template('tasks/cleaning_history.html', title='Cleaning History', sessions=sessions)


@bp.route('/property/<int:property_id>')
@login_required
def view_for_property(property_id):
    # Get the property
    property = Property.query.get_or_404(property_id)
    
    # Permission check
    can_view = False
    
    # Admin users can view all property tasks
    if current_user.has_admin_role:
        can_view = True
    # Property owners can view tasks for their properties
    elif current_user.is_property_owner and property.owner_id == current_user.id:
        can_view = True
    # Service staff can view tasks for properties they have tasks for
    elif current_user.is_service_staff:
        # Use aliases to avoid duplicate table errors
        from sqlalchemy.orm import aliased
        task_property_alias = aliased(TaskProperty)
        task_assignment_alias = aliased(TaskAssignment)
        
        # Check if the service staff has any assigned tasks for this property
        assigned_tasks = db.session.query(Task).join(
            task_property_alias, Task.id == task_property_alias.task_id
        ).filter(
            task_property_alias.property_id == property_id
        ).join(
            task_assignment_alias, Task.id == task_assignment_alias.task_id
        ).filter(
            task_assignment_alias.user_id == current_user.id
        ).first()
        
        if assigned_tasks:
            can_view = True
    
    if not can_view:
        flash('You do not have permission to view tasks for this property.', 'danger')
        return redirect(url_for('main.index'))
    
    # Get all tasks for this property
    tasks = db.session.query(Task).join(
        TaskProperty, TaskProperty.task_id == Task.id
    ).filter(
        TaskProperty.property_id == property_id
    ).order_by(Task.due_date.asc(), Task.priority.desc()).all()
    
    # If service staff, filter to only show their assigned tasks
    if current_user.is_service_staff:
        service_staff_tasks = []
        for task in tasks:
            # Check if current user is assigned to this task
            assignment = TaskAssignment.query.filter_by(
                task_id=task.id,
                user_id=current_user.id
            ).first()
            
            if assignment:
                service_staff_tasks.append(task)
        
        tasks = service_staff_tasks
    
    # Get all task assignments for these tasks
    task_ids = [task.id for task in tasks]
    assignments = {}
    
    if task_ids:
        task_assignments = TaskAssignment.query.filter(TaskAssignment.task_id.in_(task_ids)).all()
        for assignment in task_assignments:
            if assignment.task_id not in assignments:
                assignments[assignment.task_id] = []
            assignments[assignment.task_id].append(assignment)
    
    return render_template('tasks/property_tasks.html', 
                          title=f'Tasks for {property.name}',
                          property=property,
                          tasks=tasks,
                          assignments=assignments)


@bp.route('/<int:session_id>/upload_video', methods=['GET', 'POST'])
@login_required
@cleaner_required
def upload_video(session_id):
    # Get the cleaning session
    session = CleaningSession.query.get_or_404(session_id)
    
    # Check if the current user is the assigned cleaner
    if session.cleaner_id != current_user.id:
        flash('You can only upload videos for your own cleaning sessions.', 'danger')
        return redirect(url_for('tasks.index'))
    
    form = VideoUploadForm()
    
    if form.validate_on_submit():
        video_file = form.video.data
        is_start_video = form.video_type.data == 'start'
        
        # Check if a video of this type already exists
        existing_video = CleaningMedia.query.filter_by(
            cleaning_session_id=session_id,
            media_type=MediaType.VIDEO,
            is_start_video=is_start_video
        ).first()
        
        if existing_video:
            flash(f'A {"start" if is_start_video else "end"} video already exists for this session.', 'warning')
            return redirect(url_for('tasks.view', id=session.task_id))
        
        # Save the video file
        try:
            file_path, storage_backend, file_size, mime_type = save_file_to_storage(
                video_file, session_id, MediaType.VIDEO, is_start_video
            )
            
            # Create database record
            media = CleaningMedia(
                cleaning_session_id=session_id,
                media_type=MediaType.VIDEO,
                file_path=file_path,
                storage_backend=storage_backend,
                is_start_video=is_start_video,
                original_filename=video_file.filename,
                file_size=file_size,
                mime_type=mime_type
            )
            
            db.session.add(media)
            db.session.commit()
            
            flash('Video uploaded successfully!', 'success')
            return redirect(url_for('tasks.view', id=session.task_id))
            
        except Exception as e:
            flash(f'Error uploading video: {str(e)}', 'danger')
    
    return render_template('tasks/upload_video.html', 
                          title='Upload Video', 
                          form=form, 
                          session=session)


@bp.route('/<int:session_id>/report_issue', methods=['GET', 'POST'])
@login_required
@cleaner_required
def report_issue(session_id):
    # Get the cleaning session
    session = CleaningSession.query.get_or_404(session_id)
    
    # Check if the current user is the assigned cleaner
    if session.cleaner_id != current_user.id:
        flash('You can only report issues for your own cleaning sessions.', 'danger')
        return redirect(url_for('tasks.index'))
    
    form = IssueReportForm()
    
    if form.validate_on_submit():
        # Create the issue report
        issue = IssueReport(
            cleaning_session_id=session_id,
            description=form.description.data,
            location=form.location.data,
            additional_notes=form.additional_notes.data
        )
        
        db.session.add(issue)
        db.session.flush()  # Get the issue ID without committing
        
        # Handle multiple photo uploads
        photos = request.files.getlist('photos')
        
        for photo in photos:
            if photo and allowed_file(photo.filename, current_app.config['ALLOWED_PHOTO_EXTENSIONS']):
                try:
                    file_path, storage_backend, file_size, mime_type = save_file_to_storage(
                        photo, session_id, MediaType.PHOTO
                    )
                    
                    # Create media record
                    media = CleaningMedia(
                        cleaning_session_id=session_id,
                        media_type=MediaType.PHOTO,
                        file_path=file_path,
                        storage_backend=storage_backend,
                        original_filename=photo.filename,
                        file_size=file_size,
                        mime_type=mime_type
                    )
                    
                    db.session.add(media)
                    db.session.flush()
                    
                    # Associate media with issue
                    issue.media.append(media)
                    
                except Exception as e:
                    flash(f'Error uploading photo: {str(e)}', 'warning')
        
        db.session.commit()
        flash('Issue reported successfully!', 'success')
        return redirect(url_for('tasks.view', id=session.task_id))
    
    return render_template('tasks/report_issue.html', 
                          title='Report Issue', 
                          form=form, 
                          session=session)


@bp.route('/<int:session_id>/media')
@login_required
def session_media(session_id):
    # Get the cleaning session
    session = CleaningSession.query.get_or_404(session_id)
    
    # Check if user has permission to view this session
    if not (current_user.id == session.cleaner_id or 
            current_user.id == session.property.owner_id or
            current_user.is_property_owner and session.property.owner_id == current_user.id):
        flash('You do not have permission to view this media.', 'danger')
        return redirect(url_for('tasks.index'))
    
    # Get all media for this session
    videos = CleaningMedia.query.filter_by(
        cleaning_session_id=session_id,
        media_type=MediaType.VIDEO
    ).all()
    
    # Get all issue reports with their photos
    issues = IssueReport.query.filter_by(cleaning_session_id=session_id).all()
    
    return render_template('tasks/session_media.html',
                          title='Cleaning Media',
                          session=session,
                          videos=videos,
                          issues=issues)


@bp.route('/<int:session_id>/report')
@login_required
def cleaning_report(session_id):
    # Get the cleaning session
    session = CleaningSession.query.get_or_404(session_id)
    
    # Check if user has permission to view this report
    if not (current_user.id == session.cleaner_id or 
            current_user.id == session.associated_property.owner_id or
            current_user.is_property_owner and session.associated_property.owner_id == current_user.id):
        flash('You do not have permission to view this report.', 'danger')
        return redirect(url_for('tasks.index'))
    
    # Get all media for this session
    videos = CleaningMedia.query.filter_by(
        cleaning_session_id=session_id,
        media_type=MediaType.VIDEO
    ).all()
    
    # Get all issue reports
    issues = IssueReport.query.filter_by(cleaning_session_id=session_id).all()
    
    # Get inventory items used during this cleaning
    inventory_used = InventoryTransaction.query.filter(
        InventoryTransaction.user_id == session.cleaner_id,
        InventoryTransaction.transaction_type == TransactionType.USAGE,
        InventoryTransaction.created_at >= session.start_time,
        InventoryTransaction.created_at <= (session.end_time or datetime.utcnow())
    ).all()
    
    return render_template('tasks/cleaning_report.html',
                          title='Cleaning Report',
                          session=session,
                          videos=videos,
                          issues=issues,
                          inventory_used=inventory_used)


@bp.route('/repair_requests')
@login_required
def repair_requests():
    """Show repair request tasks"""
    
    # Get query parameters for sorting and filtering
    sort_by = request.args.get('sort_by', 'priority')
    property_id = request.args.get('property_id', type=int)
    
    # Base query - get tasks tagged as repair requests
    query = Task.query.filter(Task.tags.like('%repair_request%'))
    
    # Apply property filter if specified
    if property_id:
        query = query.join(
            TaskProperty, TaskProperty.task_id == Task.id
        ).filter(
            TaskProperty.property_id == property_id
        )
    
    # Apply sorting
    if sort_by == 'date':
        query = query.order_by(Task.created_at.desc())
    elif sort_by == 'due_date':
        query = query.order_by(Task.due_date)
    elif sort_by == 'property':
        query = query.join(
            TaskProperty, TaskProperty.task_id == Task.id
        ).join(
            Property, Property.id == TaskProperty.property_id
        ).order_by(Property.name)
    else:  # Default to priority
        query = query.order_by(Task.priority.desc())
    
    # Get all properties for the filter dropdown
    properties = []
    if current_user.is_property_owner:
        properties = current_user.owned_properties
    elif current_user.has_admin_role or current_user.is_property_manager:
        properties = Property.query.all()
    
    # Execute query
    repair_requests = query.all()
    
    return render_template('tasks/repair_requests.html', 
                          title='Repair Requests', 
                          repair_requests=repair_requests,
                          properties=properties,
                          current_property_id=property_id,
                          sort_by=sort_by,
                          TaskStatus=TaskStatus,
                          TaskPriority=TaskPriority)


@bp.route('/repair_requests/create', methods=['GET', 'POST'])
@login_required
def create_repair_request():
    """Create a new repair request."""
    form = RepairRequestForm()
    
    # Set up properties for the form based on user role
    if current_user.is_admin or current_user.is_property_manager:
        form.property.query_factory = lambda: Property.query.all()
    else:
        form.property.query_factory = lambda: Property.query.filter(
            Property.id.in_([p.id for p in current_user.visible_properties])
        ).all()
    
    # Pre-select property if property_id is provided
    property_id = request.args.get('property_id', type=int)
    if property_id:
        property = Property.query.get_or_404(property_id)
        if not current_user.is_admin and property not in current_user.visible_properties:
            flash('You do not have access to this property.', 'danger')
            return redirect(url_for('tasks.repair_requests'))
        form.property.data = property
    
    if form.validate_on_submit():
        try:
            # Create the task
            task = Task(
                title=form.title.data,
                description=form.description.data,
                location=form.location.data,
                status=TaskStatus.PENDING,
                priority=TaskPriority(form.priority.data.lower()) if isinstance(form.priority.data, str) else form.priority.data,
                due_date=form.due_date.data,
                notes=form.additional_notes.data,
                creator_id=current_user.id,
                tags='repair_request'
            )
            
            # Add task property
            task_property = TaskProperty(
                property_id=form.property.data.id
            )
            task.properties.append(task_property)
            
            # Handle photo uploads
            if form.photos.data:
                for photo in form.photos.data:
                    if photo and allowed_file(photo.filename):
                        try:
                            # Save the file and get the relative path
                            relative_path = save_file_to_storage(
                                photo,
                                'repair_requests',
                                task.id
                            )
                            
                            # Create TaskMedia record
                            media = TaskMedia(
                                task_id=task.id,
                                file_path=relative_path,
                                media_type=MediaType.IMAGE,
                                uploaded_by=current_user.id
                            )
                            db.session.add(media)
                            
                        except Exception as e:
                            logging.error(f"Failed to save photo for repair request {task.id}: {str(e)}")
                            flash(f'Error saving photo: {photo.filename}', 'warning')
            
            db.session.add(task)
            db.session.commit()
            
            # Send notification to property owner
            try:
                send_task_assignment_notification(task)
            except Exception as e:
                logging.error(f"Failed to send notification for repair request {task.id}: {str(e)}")
                flash('Repair request created but notification could not be sent.', 'warning')
            
            flash('Repair request created successfully!', 'success')
            return redirect(url_for('tasks.view', id=task.id))
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error creating repair request: {str(e)}")
            flash(f'Error creating repair request: {str(e)}', 'danger')
    
    return render_template('tasks/create_repair_request.html', form=form)


def can_view_task(task, user):
    """Check if a user can view a task"""
    # Admin users can view any task
    if user.has_admin_role:
        return True
        
    # Task creator can always view
    if task.creator_id == user.id:
        return True
    
    # Property owners can view tasks for their properties (if the task has properties)
    if user.is_property_owner and task.properties:
        # Get all properties owned by the user
        owned_property_ids = [p.id for p in user.properties]
        
        # Check if the task has a property_id that is owned by the user
        if task.property_id in owned_property_ids:
            return True
            
        # Also check task's associated properties
        for task_property in task.properties:
            if isinstance(task_property, int):
                if task_property in owned_property_ids:
                    return True
            elif hasattr(task_property, 'id'):
                if task_property.id in owned_property_ids:
                    return True
    
    # Users assigned to the task can view it
    for assignment in task.assignments:
        if assignment.user_id == user.id:
            return True
    
    return False


def can_edit_task(task, user):
    """Check if a user can edit a task"""
    # Admin users can edit any task
    if user.has_admin_role:
        return True
        
    # Only the creator or property owner can edit
    if task.creator_id == user.id:
        return True
    
    # Property owners can edit tasks for their properties
    if user.is_property_owner():
        # Get all properties owned by the user
        owned_property_ids = [p.id for p in user.properties]
        
        # Check if the task has a property_id that is owned by the user
        if task.property_id in owned_property_ids:
            return True
            
        # Also check task's associated properties
        for task_property in task.properties:
            if isinstance(task_property, int):
                if task_property in owned_property_ids:
                    return True
            elif hasattr(task_property, 'id'):
                if task_property.id in owned_property_ids:
                    return True
    
    return False


def can_delete_task(task, user):
    """Check if a user can delete a task"""
    # Admin users can delete any task
    if user.has_admin_role:
        return True
        
    # Only the creator can delete
    return task.creator_id == user.id


def can_complete_task(task, user):
    """Check if a user can mark a task as completed"""
    # Admin users can complete any task
    if user.has_admin_role:
        return True
        
    # Creator can complete
    if task.creator_id == user.id:
        return True
    
    # Assigned users can complete
    for assignment in task.assignments:
        if assignment.user_id == user.id:
            return True
    
    return False


def can_view_repair_request(repair_request, user):
    """Check if a user can view a repair request"""
    # Admin users can view any repair request
    if user.has_admin_role:
        return True
        
    # Reporter can always view
    if repair_request.reporter_id == user.id:
        return True
    
    # Property owner can view for their properties
    if user.is_property_owner() and repair_request.associated_property.owner_id == user.id:
        return True
    
    return False


def can_manage_repair_request(repair_request, user):
    """Check if a user can manage (approve/reject/convert) a repair request"""
    # Admin users can manage any repair request
    if user.has_admin_role:
        return True
        
    # Only property owner can manage
    return user.is_property_owner() and repair_request.associated_property.owner_id == user.id


@bp.route('/property/<int:property_id>/reorder', methods=['GET', 'POST'])
@login_required
def reorder_tasks(property_id):
    """Reorder property tasks"""
    property = Property.query.get_or_404(property_id)
    
    # Permission check - only property owners, managers and admins can reorder tasks
    if not (current_user.is_property_owner and property.owner_id == current_user.id) and \
       not current_user.is_property_manager and not current_user.has_admin_role:
        flash('You do not have permission to reorder tasks for this property.', 'danger')
        return redirect(url_for('tasks.view_for_property', property_id=property_id))
    
    # Get all tasks for this property
    property_tasks = db.session.query(Task).join(
        TaskProperty, TaskProperty.task_id == Task.id
    ).filter(
        TaskProperty.property_id == property_id
    ).order_by(Task.due_date.asc(), Task.priority.desc()).all()
    
    if request.method == 'POST':
        # Get the new order from the form submission
        task_order = request.form.getlist('task_order[]')
        
        # Update the sequence numbers
        for i, task_id in enumerate(task_order):
            task_property = TaskProperty.query.filter_by(
                task_id=task_id,
                property_id=property_id
            ).first()
            
            if task_property:
                task_property.sequence_number = i
        
        db.session.commit()
        flash('Task order has been updated successfully.', 'success')
        return redirect(url_for('tasks.view_for_property', property_id=property_id))
    
    return render_template('tasks/reorder.html',
                          title=f'Reorder Tasks for {property.name}',
                          property=property,
                          tasks=property_tasks)


@bp.route('/templates')
@login_required
def templates():
    """View and manage task templates"""
    # Get templates owned by the user or global templates
    templates = TaskTemplate.query.filter(
        db.or_(
            TaskTemplate.creator_id == current_user.id,
            TaskTemplate.is_global == True
        )
    ).order_by(TaskTemplate.sequence_number.asc()).all()
    
    return render_template('tasks/templates.html', 
                          title='Task Templates',
                          templates=templates)


@bp.route('/templates/create', methods=['GET', 'POST'])
@login_required
def create_template():
    """Create a new task template"""
    form = TaskTemplateForm()
    
    if form.validate_on_submit():
        # Get the highest sequence number for this user's templates
        max_seq = db.session.query(db.func.max(TaskTemplate.sequence_number)).filter(
            TaskTemplate.creator_id == current_user.id
        ).scalar() or 0
        
        template = TaskTemplate(
            title=form.title.data,
            description=form.description.data,
            category=form.category.data,
            is_global=form.is_global.data if current_user.has_admin_role else False,
            sequence_number=max_seq + 1,
            creator_id=current_user.id
        )
        
        db.session.add(template)
        db.session.commit()
        
        flash('Task template created successfully.', 'success')
        return redirect(url_for('tasks.templates'))
    
    return render_template('tasks/template_form.html',
                          title='Create Task Template',
                          form=form)


@bp.route('/templates/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_template(id):
    """Edit an existing task template"""
    template = TaskTemplate.query.get_or_404(id)
    
    # Check if user can edit this template
    if template.creator_id != current_user.id and not current_user.has_admin_role:
        flash('You do not have permission to edit this template.', 'danger')
        return redirect(url_for('tasks.templates'))
    
    form = TaskTemplateForm(obj=template)
    
    if form.validate_on_submit():
        template.title = form.title.data
        template.description = form.description.data
        template.category = form.category.data
        
        # Only admins can change global status
        if current_user.has_admin_role:
            template.is_global = form.is_global.data
        
        db.session.commit()
        
        flash('Task template updated successfully.', 'success')
        return redirect(url_for('tasks.templates'))
    
    return render_template('tasks/template_form.html',
                          title='Edit Task Template',
                          form=form)


@bp.route('/templates/delete/<int:id>', methods=['POST'])
@login_required
def delete_template(id):
    """Delete a task template"""
    template = TaskTemplate.query.get_or_404(id)
    
    # Check if user can delete this template
    if template.creator_id != current_user.id and not current_user.has_admin_role:
        flash('You do not have permission to delete this template.', 'danger')
        return redirect(url_for('tasks.templates'))
    
    db.session.delete(template)
    db.session.commit()
    
    flash('Task template deleted successfully.', 'success')
    return redirect(url_for('tasks.templates'))


@bp.route('/templates/reorder', methods=['POST'])
@login_required
def reorder_templates():
    """Update the order of task templates"""
    template_order = request.json.get('template_order', [])
    
    for i, template_id in enumerate(template_order):
        template = TaskTemplate.query.get(template_id)
        
        # Only update templates the user owns
        if template and (template.creator_id == current_user.id or current_user.has_admin_role):
            template.sequence_number = i
    
    db.session.commit()
    
    return jsonify({'success': True})


@bp.route('/templates/apply/<int:template_id>', methods=['GET', 'POST'])
@login_required
def apply_template(template_id):
    """Apply a task template to create a new task"""
    template = TaskTemplate.query.get_or_404(template_id)
    
    # Initialize form with template data
    form = TaskForm()
    
    # Initialize properties field with a query_factory
    if current_user.is_property_owner:
        form.properties.query_factory = lambda: Property.query.filter_by(owner_id=current_user.id).all()
    elif current_user.has_admin_role or current_user.is_property_manager:
        form.properties.query_factory = lambda: Property.query.all()
    else:
        form.properties.query_factory = lambda: []
    
    # Set up calendar choices
    calendar_choices = []
    if current_user.is_property_owner:
        for property in current_user.properties:
            for calendar in property.calendars:
                calendar_choices.append((calendar.id, f"{property.name} - {calendar.name}"))
    
    form.calendar_id.choices = [(-1, 'None')] + calendar_choices
    
    if request.method == 'GET':
        form.title.data = template.title
        form.description.data = template.description
    
    if form.validate_on_submit():
        # Create the task using form data
        task = Task(
            title=form.title.data,
            description=form.description.data,
            due_date=form.due_date.data,
            priority=TaskPriority(form.priority.data.lower()) if isinstance(form.priority.data, str) else form.priority.data,
            status=TaskStatus.PENDING,
            creator_id=current_user.id
        )
        
        # Handle recurrence if enabled
        if form.is_recurring.data:
            task.is_recurring = True
            task.recurrence_pattern = form.recurrence_pattern.data
            task.recurrence_interval = form.recurrence_interval.data
            task.recurrence_end_date = form.recurrence_end_date.data
        
        # Handle calendar link if enabled
        if form.linked_to_checkout.data and form.calendar_id.data and form.calendar_id.data != -1:
            task.linked_to_checkout = True
            task.calendar_id = form.calendar_id.data
        
        db.session.add(task)
        
        # Associate with property if selected
        if form.properties.data:
            for property_id in form.properties.data:
                task_property = TaskProperty(
                    property_id=property_id
                )
                task.properties.append(task_property)
        
        db.session.commit()
        
        flash('Task created successfully from template.', 'success')
        return redirect(url_for('tasks.view', id=task.id))
    
    return render_template('tasks/create.html', 
                           title='Create Task from Template',
                           form=form,
                           from_template=True,
                           template=template)


@bp.route('/property/<int:property_id>/create', methods=['GET', 'POST'])
@login_required
def create_task_for_property(property_id):
    """Create a new task for a specific property"""
    # Get the property
    property = Property.query.get_or_404(property_id)
    
    # Check if user has permission to create tasks for this property
    if not property.is_visible_to(current_user):
        flash('You do not have permission to create tasks for this property.', 'danger')
        return redirect(url_for('main.index'))
    
    form = TaskForm()
    
    # Initialize properties field with a query_factory
    if current_user.is_property_owner:
        form.properties.query_factory = lambda: Property.query.filter_by(owner_id=current_user.id).all()
    elif current_user.has_admin_role or current_user.is_property_manager:
        form.properties.query_factory = lambda: Property.query.all()
    else:
        form.properties.query_factory = lambda: []
        
    # Pre-select the property
    if request.method == 'GET':
        form.properties.data = [property]
    
    # Set up calendar choices
    calendar_choices = []
    for calendar in property.calendars:
        calendar_choices.append((calendar.id, f"{property.name} - {calendar.name}"))
    
    form.calendar_id.choices = [(-1, 'None')] + calendar_choices
    
    # Get suggested task templates
    task_templates = TaskTemplate.query.filter(
        db.or_(
            TaskTemplate.creator_id == current_user.id,
            TaskTemplate.is_global == True
        )
    ).order_by(TaskTemplate.sequence_number.asc()).all()
    
    if form.validate_on_submit():
        task = Task(
            title=form.title.data,
            description=form.description.data,
            due_date=form.due_date.data,
            status=TaskStatus(form.status.data),
            priority=TaskPriority(form.priority.data.lower()) if isinstance(form.priority.data, str) else form.priority.data,
            notes=form.notes.data,
            creator_id=current_user.id,
            assign_to_next_cleaner=form.assign_to_next_cleaner.data,
            property_id=property_id  # Set the property_id field directly
        )
        
        # Handle recurrence if enabled
        if form.is_recurring.data:
            task.is_recurring = True
            task.recurrence_pattern = form.recurrence_pattern.data
            task.recurrence_interval = form.recurrence_interval.data
            task.recurrence_end_date = form.recurrence_end_date.data
        
        # Handle calendar link if enabled
        if form.linked_to_checkout.data and form.calendar_id.data and form.calendar_id.data != -1:
            task.linked_to_checkout = True
            task.calendar_id = form.calendar_id.data
        
        # Associate with properties (use the selected ones from the form)
        if form.properties.data:
            for prop in form.properties.data:
                task_property = TaskProperty(
                    property_id=prop.id
                )
                task.properties.append(task_property)
        
        db.session.add(task)
        db.session.commit()
        
        flash('Task created successfully!', 'success')
        return redirect(url_for('tasks.view_for_property', property_id=property_id))
    
    return render_template('tasks/create.html', 
                          title=f'Create Task for {property.name}', 
                          form=form,
                          task_templates=task_templates,
                          property=property)


@bp.route('/workorders')
@login_required
def workorders():
    """Show workorder tasks"""
    
    # Get query parameters for sorting and filtering
    sort_by = request.args.get('sort_by', 'priority')
    property_id = request.args.get('property_id', type=int)
    
    # Base query - get tasks tagged as workorder
    query = Task.query.filter(Task.tags.contains('workorder'))
    
    # Apply property filter if specified
    if property_id:
        query = query.join(
            TaskProperty, TaskProperty.task_id == Task.id
        ).filter(
            TaskProperty.property_id == property_id
        )
    
    # Apply sorting
    if sort_by == 'date':
        query = query.order_by(Task.created_at.desc())
    elif sort_by == 'due_date':
        query = query.order_by(Task.due_date)
    elif sort_by == 'property':
        # This is more complex as we need to sort by property name
        query = query.join(
            TaskProperty, TaskProperty.task_id == Task.id
        ).join(
            Property, Property.id == TaskProperty.property_id
        ).order_by(Property.name)
    else:  # Default to priority
        query = query.order_by(Task.priority.desc())
    
    # Get all properties for the filter dropdown
    properties = []
    if current_user.is_property_owner:
        properties = current_user.owned_properties
    elif current_user.has_admin_role or current_user.is_property_manager:
        properties = Property.query.all()
    
    # Execute query
    workorders = query.all()
    
    return render_template('tasks/workorders.html', 
                          title='Work Orders', 
                          workorders=workorders,
                          properties=properties,
                          current_property_id=property_id,
                          sort_by=sort_by)


@bp.route('/workorders/create', methods=['GET', 'POST'])
@login_required
def create_workorder():
    """Create a new workorder"""
    form = TaskForm()
    
    # Set up the form
    form.properties.query = Property.query
    
    # Process form submission
    if form.validate_on_submit():
        # Create the task
        task = Task(
            title=form.title.data,
            description=form.description.data,
            status=TaskStatus(form.status.data),
            priority=TaskPriority(form.priority.data.lower()) if isinstance(form.priority.data, str) else form.priority.data,
            due_date=form.due_date.data,
            creator_id=current_user.id,
            notes=form.notes.data,
            is_recurring=form.is_recurring.data,
            recurrence_pattern=form.recurrence_pattern.data if form.is_recurring.data else None,
            recurrence_interval=form.recurrence_interval.data if form.is_recurring.data else 1,
            recurrence_end_date=form.recurrence_end_date.data,
            linked_to_checkout=form.linked_to_checkout.data,
            calendar_id=form.calendar_id.data if form.linked_to_checkout.data else None,
            assign_to_next_cleaner=form.assign_to_next_cleaner.data,
            tags='workorder'  # Always tag as workorder
        )
        
        # Add any additional tags if specified
        if form.tags.data:
            tags = [tag.strip() for tag in form.tags.data.split(',')]
            if 'workorder' not in tags:
                tags.append('workorder')
            task.tags = ','.join(tags)
        
        db.session.add(task)
        
        # Add properties
        if form.properties.data:
            for property in form.properties.data:
                task.add_property(property.id)
        
        db.session.commit()
        
        flash('Work order created successfully!', 'success')
        return redirect(url_for('tasks.workorders'))
    
    # Default form values
    form.status.data = TaskStatus.PENDING
    form.priority.data = TaskPriority.MEDIUM
    form.recurrence_pattern.data = RecurrencePattern.NONE
    
    return render_template('tasks/create_workorder.html', 
                         title='Create Work Order',
                         form=form)