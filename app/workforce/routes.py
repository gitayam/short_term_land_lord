from flask import render_template, redirect, url_for, flash, request, current_app, abort, jsonify
from flask_login import login_required, current_user
from app import db
from app.workforce import bp
from app.workforce.forms import WorkerInvitationForm, WorkerPropertyAssignmentForm, WorkerFilterForm
from app.models import User, Property, Task, TaskAssignment, TaskProperty, UserRoles, ServiceType, TaskStatus
from app.auth.decorators import admin_required, property_manager_required, workforce_management_required
from app.auth.email import send_email
from app.notifications.service import create_notification, NotificationType, NotificationChannel
from sqlalchemy import or_, and_
from datetime import datetime, timedelta
import secrets
import string

# Helper function to check if a worker is assigned to a property
def is_worker_assigned_to_property(worker_id, property_id):
    """Check if a worker is assigned to a property by looking at task assignments"""
    # Look for any task assignment where the worker is assigned to a task for this property
    assignment = db.session.query(TaskAssignment).join(
        Task, TaskAssignment.task_id == Task.id
    ).join(
        TaskProperty, TaskProperty.task_id == Task.id
    ).filter(
        TaskAssignment.user_id == worker_id,
        TaskProperty.property_id == property_id
    ).first()
    
    return assignment is not None

# Helper function to get all properties a worker is assigned to
def get_worker_properties(worker_id):
    """Get all properties a worker is assigned to"""
    property_ids = db.session.query(Property.id).join(
        TaskProperty, Property.id == TaskProperty.property_id
    ).join(
        Task, TaskProperty.task_id == Task.id
    ).join(
        TaskAssignment, Task.id == TaskAssignment.task_id
    ).filter(
        TaskAssignment.user_id == worker_id
    ).distinct().all()
    
    return [id[0] for id in property_ids]

# Helper function to get all workers assigned to a property
def get_property_workers(property_id):
    """Get all workers assigned to a property"""
    worker_ids = db.session.query(User.id).join(
        TaskAssignment, User.id == TaskAssignment.user_id
    ).join(
        Task, TaskAssignment.task_id == Task.id
    ).join(
        TaskProperty, Task.id == TaskProperty.task_id
    ).filter(
        TaskProperty.property_id == property_id,
        User.role == UserRoles.SERVICE_STAFF
    ).distinct().all()
    
    return [id[0] for id in worker_ids]

# Helper function to generate a random password
def generate_password(length=12):
    """Generate a random password"""
    alphabet = string.ascii_letters + string.digits + string.punctuation
    return ''.join(secrets.choice(alphabet) for i in range(length))

@bp.route('/')
@login_required
def index():
    """Main workforce dashboard - shows different views based on user role"""
    if current_user.is_admin() or current_user.is_property_manager() or current_user.is_property_owner():
        # Admin/manager view - show all service staff
        form = WorkerFilterForm()
        
        # Set up property choices for the filter form
        if current_user.is_property_owner():
            # Property owners only see their properties
            properties = Property.query.filter_by(owner_id=current_user.id).all()
        else:
            # Admins and managers see all properties
            properties = Property.query.all()
            
        form.property_id.choices = [(-1, 'All Properties')] + [(p.id, p.name) for p in properties]
        
        # Base query for service staff
        query = User.query.filter_by(role=UserRoles.SERVICE_STAFF)
        
        # Apply filters if form is submitted
        if request.args.get('submit'):
            # Filter by service type if provided
            service_type = request.args.get('service_type')
            if service_type:
                # This is more complex - we need to look at task assignments
                worker_ids = db.session.query(TaskAssignment.user_id).filter(
                    TaskAssignment.service_type == service_type
                ).distinct().all()
                worker_ids = [id[0] for id in worker_ids]
                if worker_ids:
                    query = query.filter(User.id.in_(worker_ids))
                else:
                    # No workers match this service type
                    query = query.filter(User.id == -1)  # This will return no results
            
            # Filter by property if provided
            property_id = request.args.get('property_id')
            if property_id and property_id != '-1':
                # Get workers assigned to this property
                worker_ids = get_property_workers(int(property_id))
                if worker_ids:
                    query = query.filter(User.id.in_(worker_ids))
                else:
                    # No workers assigned to this property
                    query = query.filter(User.id == -1)  # This will return no results
            
            # Filter by search term if provided
            search = request.args.get('search')
            if search:
                query = query.filter(or_(
                    User.first_name.ilike(f'%{search}%'),
                    User.last_name.ilike(f'%{search}%'),
                    User.email.ilike(f'%{search}%')
                ))
        
        # Get workers with pagination
        page = request.args.get('page', 1, type=int)
        workers = query.paginate(page=page, per_page=10)
        
        # For each worker, get their assigned properties
        worker_properties = {}
        for worker in workers.items:
            worker_properties[worker.id] = get_worker_properties(worker.id)
        
        return render_template('workforce/admin_dashboard.html',
                              title='Workforce Management',
                              workers=workers,
                              worker_properties=worker_properties,
                              form=form)
    
    elif current_user.is_service_staff():
        # Service staff view - show their tasks and assigned properties
        # Get tasks assigned to this worker
        pending_tasks = db.session.query(Task).join(
            TaskAssignment, TaskAssignment.task_id == Task.id
        ).filter(
            TaskAssignment.user_id == current_user.id,
            Task.status == TaskStatus.PENDING
        ).order_by(Task.due_date.asc()).all()
        
        in_progress_tasks = db.session.query(Task).join(
            TaskAssignment, TaskAssignment.task_id == Task.id
        ).filter(
            TaskAssignment.user_id == current_user.id,
            Task.status == TaskStatus.IN_PROGRESS
        ).all()
        
        completed_tasks = db.session.query(Task).join(
            TaskAssignment, TaskAssignment.task_id == Task.id
        ).filter(
            TaskAssignment.user_id == current_user.id,
            Task.status == TaskStatus.COMPLETED
        ).order_by(Task.completed_at.desc()).limit(10).all()
        
        # Get properties this worker is assigned to
        property_ids = get_worker_properties(current_user.id)
        assigned_properties = Property.query.filter(Property.id.in_(property_ids)).all() if property_ids else []
        
        return render_template('workforce/staff_dashboard.html',
                              title='My Dashboard',
                              pending_tasks=pending_tasks,
                              in_progress_tasks=in_progress_tasks,
                              completed_tasks=completed_tasks,
                              assigned_properties=assigned_properties)
    
    # Fallback for other roles
    flash('You do not have access to the workforce management section.', 'danger')
    return redirect(url_for('main.index'))

@bp.route('/invite', methods=['GET', 'POST'])
@login_required
@workforce_management_required
def invite_worker():
    """Invite a new service staff member"""
    form = WorkerInvitationForm()
    
    if form.validate_on_submit():
        # Generate a random password for the new user
        password = generate_password()
        
        # Create the new user
        user = User(
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            email=form.email.data,
            role=UserRoles.SERVICE_STAFF
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        # Send invitation email with login credentials
        send_worker_invitation(user, password, form.service_type.data, form.message.data)
        
        flash(f'Invitation sent to {user.get_full_name()} ({user.email}).', 'success')
        return redirect(url_for('workforce.index'))
    
    return render_template('workforce/invite_worker.html',
                          title='Invite Service Staff',
                          form=form)

def send_worker_invitation(user, password, service_type, custom_message=None):
    """Send an invitation email to a new service staff member"""
    service_type_display = dict((t.value, t.name) for t in ServiceType).get(service_type, service_type)
    
    subject = 'You have been invited to join the Property Management System'
    
    # Create email body
    body = f"""
    Dear {user.get_full_name()},
    
    You have been invited to join our Property Management System as a {service_type_display} staff member.
    
    Your login credentials are:
    Email: {user.email}
    Password: {password}
    
    Please log in at {request.host_url} and change your password as soon as possible.
    """
    
    if custom_message:
        body += f"\n\nAdditional message from the administrator:\n{custom_message}"
    
    # Send the email
    send_email(subject, sender=current_app.config['MAIL_DEFAULT_SENDER'], recipients=[user.email], text_body=body)
    
    # Also create an in-app notification
    create_notification(
        user_id=user.id,
        notification_type=NotificationType.TASK_ASSIGNMENT,
        channel=NotificationChannel.IN_APP,
        title='Welcome to the Property Management System',
        message=f'You have been added as a {service_type_display} staff member. Please update your profile and change your password.'
    )

@bp.route('/assign', methods=['GET', 'POST'])
@login_required
@workforce_management_required
def assign_properties():
    """Assign workers to properties"""
    form = WorkerPropertyAssignmentForm()
    
    # Property owners can only assign to their own properties
    if current_user.is_property_owner():
        form.properties.query = Property.query.filter_by(owner_id=current_user.id)
    
    if form.validate_on_submit():
        worker = form.worker.data
        properties = form.properties.data
        service_type = ServiceType(form.service_type.data)
        
        if not worker:
            flash('Please select a worker to assign properties.', 'danger')
            return redirect(url_for('workforce.assign_properties'))
        
        if not properties:
            flash('Please select at least one property to assign.', 'danger')
            return redirect(url_for('workforce.assign_properties'))
        
        # For each property, create a placeholder task to establish the worker-property relationship
        for property in properties:
            # Check if worker is already assigned to this property
            if is_worker_assigned_to_property(worker.id, property.id):
                continue
                
            # Create a placeholder task for this property
            task = Task(
                title=f"{service_type.name} Assignment for {property.name}",
                description=f"This task establishes {worker.get_full_name()} as a {service_type.name} for {property.name}.",
                status=TaskStatus.PENDING,
                creator_id=current_user.id
            )
            
            # Associate task with property
            task_property = TaskProperty(property=property)
            task.properties.append(task_property)
            
            # Assign worker to task
            task_assignment = TaskAssignment(
                user_id=worker.id,
                service_type=service_type
            )
            task.assignments.append(task_assignment)
            
            db.session.add(task)
        
        db.session.commit()
        
        flash(f'Successfully assigned {worker.get_full_name()} to {len(properties)} properties.', 'success')
        return redirect(url_for('workforce.index'))
    
    return render_template('workforce/assign_properties.html',
                          title='Assign Properties to Worker',
                          form=form)

@bp.route('/worker/<int:id>')
@login_required
@workforce_management_required
def worker_detail(id):
    """View details for a specific worker"""
    worker = User.query.get_or_404(id)
    
    # Ensure the user is a service staff member
    if not worker.is_service_staff():
        flash('This user is not a service staff member.', 'danger')
        return redirect(url_for('workforce.index'))
    
    # Get properties this worker is assigned to
    property_ids = get_worker_properties(worker.id)
    assigned_properties = Property.query.filter(Property.id.in_(property_ids)).all() if property_ids else []
    
    # Get tasks assigned to this worker
    pending_tasks = db.session.query(Task).join(
        TaskAssignment, TaskAssignment.task_id == Task.id
    ).filter(
        TaskAssignment.user_id == worker.id,
        Task.status == TaskStatus.PENDING
    ).order_by(Task.due_date.asc()).all()
    
    in_progress_tasks = db.session.query(Task).join(
        TaskAssignment, TaskAssignment.task_id == Task.id
    ).filter(
        TaskAssignment.user_id == worker.id,
        Task.status == TaskStatus.IN_PROGRESS
    ).all()
    
    completed_tasks = db.session.query(Task).join(
        TaskAssignment, TaskAssignment.task_id == Task.id
    ).filter(
        TaskAssignment.user_id == worker.id,
        Task.status == TaskStatus.COMPLETED
    ).order_by(Task.completed_at.desc()).limit(10).all()
    
    # Get service types this worker provides
    service_types = db.session.query(TaskAssignment.service_type).filter(
        TaskAssignment.user_id == worker.id,
        TaskAssignment.service_type.isnot(None)
    ).distinct().all()
    service_types = [st[0] for st in service_types]
    
    return render_template('workforce/worker_detail.html',
                          title=f'Worker: {worker.get_full_name()}',
                          worker=worker,
                          assigned_properties=assigned_properties,
                          pending_tasks=pending_tasks,
                          in_progress_tasks=in_progress_tasks,
                          completed_tasks=completed_tasks,
                          service_types=service_types)

@bp.route('/my-properties')
@login_required
def my_properties():
    """View properties assigned to the current worker"""
    if not current_user.is_service_staff():
        flash('This page is only available to service staff.', 'danger')
        return redirect(url_for('workforce.index'))
    
    # Get properties this worker is assigned to
    property_ids = get_worker_properties(current_user.id)
    assigned_properties = Property.query.filter(Property.id.in_(property_ids)).all() if property_ids else []
    
    return render_template('workforce/my_properties.html',
                          title='My Assigned Properties',
                          assigned_properties=assigned_properties)

@bp.route('/my-tasks')
@login_required
def my_tasks():
    """View tasks assigned to the current worker"""
    if not current_user.is_service_staff():
        flash('This page is only available to service staff.', 'danger')
        return redirect(url_for('workforce.index'))
    
    # Get tasks assigned to this worker
    status_filter = request.args.get('status', 'pending')
    
    if status_filter == 'pending':
        tasks = db.session.query(Task).join(
            TaskAssignment, TaskAssignment.task_id == Task.id
        ).filter(
            TaskAssignment.user_id == current_user.id,
            Task.status == TaskStatus.PENDING
        ).order_by(Task.due_date.asc()).all()
        title = 'My Pending Tasks'
    elif status_filter == 'in_progress':
        tasks = db.session.query(Task).join(
            TaskAssignment, TaskAssignment.task_id == Task.id
        ).filter(
            TaskAssignment.user_id == current_user.id,
            Task.status == TaskStatus.IN_PROGRESS
        ).all()
        title = 'My In-Progress Tasks'
    elif status_filter == 'completed':
        tasks = db.session.query(Task).join(
            TaskAssignment, TaskAssignment.task_id == Task.id
        ).filter(
            TaskAssignment.user_id == current_user.id,
            Task.status == TaskStatus.COMPLETED
        ).order_by(Task.completed_at.desc()).all()
        title = 'My Completed Tasks'
    else:
        tasks = db.session.query(Task).join(
            TaskAssignment, TaskAssignment.task_id == Task.id
        ).filter(
            TaskAssignment.user_id == current_user.id
        ).all()
        title = 'All My Tasks'
    
    return render_template('workforce/my_tasks.html',
                          title=title,
                          tasks=tasks,
                          status_filter=status_filter)

@bp.route('/my-invoices')
@login_required
def my_invoices():
    """View invoices related to the current worker"""
    if not current_user.is_service_staff():
        flash('This page is only available to service staff.', 'danger')
        return redirect(url_for('workforce.index'))
    
    # This requires integration with the invoicing system
    # For now, we'll just redirect to a placeholder template
    return render_template('workforce/my_invoices.html',
                          title='My Invoices')