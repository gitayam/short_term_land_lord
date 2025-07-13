from flask import render_template, redirect, url_for, flash, request, current_app, abort, jsonify
from flask_login import login_required, current_user
from app import db
from app.workforce import bp
from app.workforce.forms import WorkerInvitationForm, WorkerPropertyAssignmentForm, WorkerFilterForm, COUNTRY_CODES
from app.models import User, Property, Task, TaskAssignment, TaskProperty, UserRoles, ServiceType, TaskStatus, AdminAction, Notification
from app.auth.decorators import admin_required, property_manager_required, workforce_management_required
from app.auth.email import send_email, send_password_reset_email
from app.notifications.service import create_notification, NotificationType, NotificationChannel
from app.utils.error_handling import handle_errors, ValidationError, BusinessLogicError
from app.utils.validation import InputValidator
from sqlalchemy import or_, and_
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta
import secrets
import string
from app.decorators import log_admin_action

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
        User.role == UserRoles.SERVICE_STAFF.value
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
    if current_user.is_admin or current_user.is_property_manager or current_user.is_property_owner:
        # Admin/manager view - show all service staff
        form = WorkerFilterForm()
        
        # Set up property choices for the filter form
        if current_user.is_property_owner:
            # Property owners only see their properties
            properties = Property.query.filter_by(owner_id=current_user.id).all()
        else:
            # Admins and managers see all properties
            properties = Property.query.all()
            
        form.property_id.choices = [(-1, 'All Properties')] + [(p.id, p.name) for p in properties]
        
        # Base query for service staff
        query = User.query.filter(User.role == UserRoles.SERVICE_STAFF.value)
        
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
                              form=form,
                              TaskAssignment=TaskAssignment)
    
    elif current_user.is_service_staff:
        # Service staff view - show their tasks and assigned properties
        # Get tasks assigned to this worker
        pending_tasks = db.session.query(Task).join(
            TaskAssignment, TaskAssignment.task_id == Task.id
        ).outerjoin(
            TaskProperty, Task.id == TaskProperty.task_id
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
            phone=form.phone.data,
            role=UserRoles.SERVICE_STAFF.value
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        # Get service type display name
        service_type_display = dict((t.value, t.name) for t in ServiceType).get(form.service_type.data, form.service_type.data)
        
        # Send invitation via selected channels
        delivery_status = {'email': False, 'sms': False}
        error_messages = []
        
        # Send email if requested
        if form.send_email.data:
            try:
                send_worker_invitation(user, password, form.service_type.data, form.message.data)
                delivery_status['email'] = True
            except Exception as e:
                error_messages.append(f'Email delivery failed: {str(e)}')
        
        # Send SMS if requested
        if form.send_sms.data and form.phone.data:
            try:
                from app.utils.sms import send_sms
                # Get the country code prefix
                country_code = next((code[1].split(' ')[0] for code in COUNTRY_CODES if code[0] == form.country_code.data), '+1')
                # Format the phone number with country code
                phone_number = form.phone.data.strip()
                # Remove any non-digit characters except +
                phone_number = ''.join(c for c in phone_number if c.isdigit() or c == '+')
                # Remove any existing country code from the phone number
                if phone_number.startswith('+'):
                    phone_number = phone_number[1:]
                # Ensure proper E.164 format
                full_phone = f"{country_code}{phone_number}"
                
                message = (
                    f"Hi {user.first_name}, you've been invited to join Short Term Landlord as a {service_type_display} staff member. "
                    f"Please check your email ({user.email}) for your login credentials and registration link. "
                    f"Contact support@shorttermlandlord.com if you have any questions."
                )
                
                # Log the SMS attempt
                current_app.logger.info(f"Attempting to send SMS to {full_phone}")
                success, error = send_sms(full_phone, message)
                
                if success:
                    delivery_status['sms'] = True
                    current_app.logger.info(f"SMS sent successfully to {full_phone}")
                else:
                    # Only show SMS errors as warnings, not critical errors
                    if "SMS disabled" in error:
                        current_app.logger.info(f"SMS not sent: {error}")
                    else:
                        error_messages.append(f'SMS delivery failed: {error}')
                        current_app.logger.error(f"SMS delivery failed: {error}")
            except Exception as e:
                error_msg = f'SMS delivery failed: {str(e)}'
                error_messages.append(error_msg)
                current_app.logger.error(error_msg)
        
        # Prepare flash message based on delivery status
        if delivery_status['email'] or delivery_status['sms']:
            status_msg = []
            if delivery_status['email']:
                status_msg.append('email')
            if delivery_status['sms']:
                status_msg.append('SMS')
            flash(f'Invitation sent to {user.get_full_name()} via {", ".join(status_msg)}.', 'success')
        else:
            flash('Failed to send invitation. Please try again.', 'danger')
        
        if error_messages:
            for error in error_messages:
                flash(error, 'warning')
        
        return redirect(url_for('workforce.index'))
    
    return render_template('workforce/invite_worker.html',
                          title='Invite Service Staff',
                          form=form)

def send_worker_invitation(user, password, service_type, custom_message=None):
    """Send an invitation email to a new service staff member"""
    service_type_display = dict((t.value, t.name) for t in ServiceType).get(service_type, service_type)
    
    subject = 'You have been invited to join the Property Management System'
    
    # Create email context
    context = {
        'user': user,
        'inviter': current_user,
        'service_type_display': service_type_display,
        'password': password,
        'message': custom_message,
        'now': datetime.utcnow()
    }
    
    # Send the email with both HTML and plain text versions
    send_email(
        subject=subject,
        recipients=[user.email],
        text_body=render_template('email/service_staff_invite.txt', **context),
        html_body=render_template('email/service_staff_invite.html', **context)
    )
    
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
@handle_errors
def assign_properties():
    """Assign workers to properties"""
    form = WorkerPropertyAssignmentForm()
    
    # Property owners can only assign to their own properties
    if current_user.is_property_owner:
        form.properties.query = Property.query.filter_by(owner_id=current_user.id)
    
    if form.validate_on_submit():
        worker = form.worker.data
        properties = form.properties.data
        service_type = form.service_type.data
        
        # Additional validation using our validation utilities
        validator = InputValidator()
        
        if not worker:
            validator.add_error('worker', 'Please select a worker to assign properties.')
        
        if not properties:
            validator.add_error('properties', 'Please select at least one property to assign.')
        
        if not validator.is_valid():
            for error in validator.get_errors():
                flash(error['message'], 'danger')
            return render_template('workforce/assign_properties.html',
                                  title='Assign Properties to Worker',
                                  form=form)
        
        try:
            assigned_count = 0
            
            # For each property, create a placeholder task to establish the worker-property relationship
            for property in properties:
                # Check if worker is already assigned to this property
                if is_worker_assigned_to_property(worker.id, property.id):
                    current_app.logger.info(f"Worker {worker.id} already assigned to property {property.id}, skipping")
                    continue
                    
                # Create a placeholder task for this property
                task = Task(
                    title=f"{service_type.name} Assignment for {property.name}",
                    description=f"This task establishes {worker.get_full_name()} as a {service_type.name} for {property.name}.",
                    status=TaskStatus.PENDING,
                    creator_id=current_user.id
                )
                
                # Add task to session first to get an ID
                db.session.add(task)
                db.session.flush()  # This will assign an ID to the task without committing
                
                # Validate that task has an ID
                if not task.id:
                    raise BusinessLogicError("Failed to create task - no ID assigned")
                
                # Now create the task_property with the task's ID
                task_property = TaskProperty(
                    task_id=task.id,
                    property_id=property.id,
                    sequence_number=0
                )
                db.session.add(task_property)
                
                # Assign worker to task
                task_assignment = TaskAssignment(
                    task_id=task.id,
                    user_id=worker.id,
                    service_type=service_type
                )
                db.session.add(task_assignment)
                assigned_count += 1
            
            # Only commit if we have assignments to save
            if assigned_count > 0:
                db.session.commit()
                flash(f'Successfully assigned {worker.get_full_name()} to {assigned_count} properties.', 'success')
                current_app.logger.info(f"Assigned worker {worker.id} to {assigned_count} properties by user {current_user.id}")
            else:
                db.session.rollback()
                flash(f'{worker.get_full_name()} is already assigned to all selected properties.', 'info')
            
            return redirect(url_for('workforce.index'))
            
        except IntegrityError as e:
            db.session.rollback()
            current_app.logger.error(f"Database integrity error in assign_properties: {str(e)}")
            flash('Failed to assign worker due to database constraint violation. Please try again.', 'danger')
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Unexpected error in assign_properties: {str(e)}")
            flash('An unexpected error occurred while assigning worker to properties. Please try again.', 'danger')
    
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
    if not worker.is_service_staff:
        flash('This user is not a service staff member.', 'danger')
        return redirect(url_for('workforce.index'))
    
    # Get properties this worker is assigned to
    property_ids = get_worker_properties(worker.id)
    assigned_properties = Property.query.filter(Property.id.in_(property_ids)).all() if property_ids else []
    
    # Get tasks assigned to this worker
    pending_tasks = db.session.query(Task).join(
        TaskAssignment, TaskAssignment.task_id == Task.id
    ).outerjoin(
        TaskProperty, Task.id == TaskProperty.task_id
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
    if not current_user.is_service_staff:
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
    if not current_user.is_service_staff:
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
    if not current_user.is_service_staff:
        flash('This page is only available to service staff.', 'danger')
        return redirect(url_for('workforce.index'))
    
    # This requires integration with the invoicing system
    # For now, we'll just redirect to a placeholder template
    return render_template('workforce/my_invoices.html',
                          title='My Invoices')

@bp.route('/api/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_staff(user_id):
    """Delete a staff member's account"""
    user = User.query.get_or_404(user_id)
    
    if user.is_admin or user.is_property_manager:
        return jsonify({'success': False, 'message': 'Cannot delete admin or manager accounts'}), 403
    
    try:
        # Log the action before deletion
        admin_action = AdminAction(
            admin_id=current_user.id,
            target_user_id=user.id,
            action_type='delete',
            action_details=f'Deleted user account for {user.email}',
            ip_address=request.remote_addr
        )
        db.session.add(admin_action)
        
        # Delete related records first
        TaskAssignment.query.filter_by(user_id=user.id).delete()
        Notification.query.filter_by(recipient_id=user.id).delete()
        
        # Delete the user
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'User account deleted successfully'})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error deleting user {user_id}: {str(e)}')
        return jsonify({'success': False, 'message': 'Failed to delete user account'}), 500

@bp.route('/api/<int:user_id>/reset-password', methods=['POST'])
@login_required
@admin_required
def reset_staff_password(user_id):
    """Reset a staff member's password"""
    user = User.query.get_or_404(user_id)
    
    try:
        # Generate password reset token
        send_password_reset_email(user)
        
        # Log the action
        admin_action = AdminAction(
            admin_id=current_user.id,
            target_user_id=user.id,
            action_type='reset_password',
            action_details=f'Initiated password reset for {user.email}',
            ip_address=request.remote_addr
        )
        db.session.add(admin_action)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Password reset email sent'})
    except Exception as e:
        current_app.logger.error(f'Error resetting password for user {user_id}: {str(e)}')
        return jsonify({'success': False, 'message': 'Failed to send password reset email'}), 500

@bp.route('/api/<int:user_id>/toggle-suspension', methods=['POST'])
@login_required
@admin_required
def toggle_staff_suspension(user_id):
    """Toggle suspension status of a staff member"""
    user = User.query.get_or_404(user_id)
    
    if user.is_admin or user.is_property_manager:
        return jsonify({'success': False, 'message': 'Cannot suspend admin or manager accounts'}), 403
    
    try:
        action_type = 'reactivate' if user.is_suspended else 'suspend'
        if action_type == 'suspend':
            user.suspend()
        else:
            user.reactivate()
        
        # Log the action
        admin_action = AdminAction(
            admin_id=current_user.id,
            target_user_id=user.id,
            action_type=action_type,
            action_details=f'{action_type.capitalize()}d user account {user.email}',
            ip_address=request.remote_addr
        )
        db.session.add(admin_action)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'User account {"suspended" if user.is_suspended else "reactivated"} successfully',
            'is_suspended': user.is_suspended
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error toggling suspension for user {user_id}: {str(e)}')
        return jsonify({'success': False, 'message': 'Failed to update user status'}), 500

@bp.route('/api/<int:user_id>/resend-invite', methods=['POST'])
@login_required
@admin_required
def resend_staff_invite(user_id):
    """Resend invitation to a staff member"""
    user = User.query.get_or_404(user_id)
    
    try:
        # Generate a new password
        password = generate_password()
        user.set_password(password)
        
        # Send invitation
        send_worker_invitation(user, password, user.service_type)
        
        # Log the action
        admin_action = AdminAction(
            admin_id=current_user.id,
            target_user_id=user.id,
            action_type='resend_invite',
            action_details=f'Resent invitation to {user.email}',
            ip_address=request.remote_addr
        )
        db.session.add(admin_action)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Invitation resent successfully'})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error resending invite to user {user_id}: {str(e)}')
        return jsonify({'success': False, 'message': 'Failed to resend invitation'}), 500

@bp.route('/api/<int:user_id>/audit-log', methods=['GET'])
@login_required
@admin_required
def get_staff_audit_log(user_id):
    """Get audit log for a staff member"""
    try:
        actions = AdminAction.query.filter_by(target_user_id=user_id)\
            .order_by(AdminAction.created_at.desc())\
            .limit(50)\
            .all()
        
        return jsonify({
            'success': True,
            'logs': [{
                'action_type': action.action_type,
                'details': action.action_details,
                'admin': action.admin.get_full_name(),
                'timestamp': action.created_at.isoformat(),
                'ip_address': action.ip_address
            } for action in actions]
        })
    except Exception as e:
        current_app.logger.error(f'Error fetching audit log for user {user_id}: {str(e)}')
        return jsonify({'success': False, 'message': 'Failed to fetch audit log'}), 500

@bp.route('/api/<int:user_id>/manual-confirm', methods=['POST'])
@login_required
@admin_required
@log_admin_action
def manual_confirm(user_id):
    """Manually confirm a user's account"""
    user = User.query.get_or_404(user_id)
    
    if user.confirmed:
        return jsonify({'success': False, 'message': 'User is already confirmed'}), 400
    
    try:
        # Generate a new password for the user
        password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))
        user.set_password(password)
        
        # Mark the user as confirmed
        user.confirmed = True
        user.confirmed_at = datetime.utcnow()
        
        # Create admin action log
        admin_action = AdminAction(
            admin_id=current_user.id,
            target_user_id=user.id,
            action_type='manual_confirm',
            action_details=f'Manually confirmed user account for {user.email}',
            ip_address=request.remote_addr
        )
        db.session.add(admin_action)
        
        # Create notification for the user
        create_notification(
            recipient_id=user.id,
            notification_type=NotificationType.ACCOUNT_CONFIRMED,
            title='Your account has been confirmed',
            message=f'Your account has been manually confirmed by an administrator. Your temporary password is: {password}',
            channel=NotificationChannel.EMAIL
        )
        
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': 'User account confirmed successfully. A notification with login credentials has been sent.'
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error confirming user {user_id}: {str(e)}')
        return jsonify({'success': False, 'message': 'Failed to confirm user account'}), 500