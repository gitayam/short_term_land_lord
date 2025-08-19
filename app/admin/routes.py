from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import (SiteSetting, User, UserRoles, RepairRequest, RepairRequestStatus, 
                       Property, RegistrationRequest, ApprovalStatus, UserNote, UserAccountAction)
from app.admin.forms import SiteSettingsForm, RequestReviewForm
from app.auth.decorators import admin_required
from app.auth.email import send_email
from app.admin import bp
import secrets
import string

@bp.route('/settings', methods=['GET', 'POST'])
@login_required
@admin_required
def settings():
    """Manage site settings"""
    form = SiteSettingsForm()
    
    if form.validate_on_submit():
        # Update OpenAI API key
        SiteSetting.set_setting('openai_api_key', form.openai_api_key.data, 'OpenAI API Key for AI functionality', False)
        
        # Update guest reviews setting
        SiteSetting.set_setting('guest_reviews_enabled', str(form.enable_guest_reviews.data).lower(), 'Enable guest reviews feature', True)
        
        flash('Settings updated successfully!', 'success')
        return redirect(url_for('admin.settings'))
    
    elif request.method == 'GET':
        # Get current settings
        openai_api_key = SiteSetting.get_setting('openai_api_key')
        if openai_api_key:
            form.openai_api_key.data = openai_api_key
        
        guest_reviews_enabled = SiteSetting.get_setting('guest_reviews_enabled')
        if guest_reviews_enabled:
            form.enable_guest_reviews.data = guest_reviews_enabled.lower() == 'true'
    
    # Get all public settings for display
    public_settings = SiteSetting.query.filter_by(visible=True).all()
    
    return render_template('admin/settings.html', 
                          form=form, 
                          settings=public_settings,
                          title='Site Settings')

@bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """Admin dashboard with simple stats"""
    # Get counts of different user roles
    user_count = User.query.count()
    owner_count = User.query.filter_by(role=UserRoles.PROPERTY_OWNER.value).count()
    manager_count = User.query.filter_by(role=UserRoles.PROPERTY_MANAGER.value).count()
    staff_count = User.query.filter_by(role=UserRoles.SERVICE_STAFF.value).count()
    
    # Get pending registration requests count
    pending_registrations = RegistrationRequest.query.filter_by(status=ApprovalStatus.PENDING).count()
    
    # Get pending and recently created repair requests
    pending_requests = RepairRequest.query.filter(
        RepairRequest.status.in_([
            RepairRequestStatus.PENDING, 
            RepairRequestStatus.APPROVED
        ])
    ).order_by(RepairRequest.created_at.desc()).limit(10).all()
    
    # Preload property data to avoid N+1 queries
    property_dict = {}
    property_ids = [req.property_id for req in pending_requests]
    if property_ids:
        properties = Property.query.filter(Property.id.in_(property_ids)).all()
        property_dict = {prop.id: prop for prop in properties}
    
    return render_template('admin/dashboard.html',
                          user_count=user_count,
                          owner_count=owner_count,
                          manager_count=manager_count,
                          staff_count=staff_count,
                          pending_registrations=pending_registrations,
                          pending_requests=pending_requests,
                          property_dict=property_dict,
                          title='Admin Dashboard')

@bp.route('/registrations')
@login_required
@admin_required
def registrations():
    """View and manage registration requests"""
    # Get status filter, default to pending
    status = request.args.get('status', 'pending')
    
    if status == 'pending':
        requests = RegistrationRequest.query.filter_by(status=ApprovalStatus.PENDING).order_by(
            RegistrationRequest.created_at.desc()).all()
        title = 'Pending Registration Requests'
    elif status == 'approved':
        requests = RegistrationRequest.query.filter_by(status=ApprovalStatus.APPROVED).order_by(
            RegistrationRequest.updated_at.desc()).all()
        title = 'Approved Registration Requests'
    elif status == 'rejected':
        requests = RegistrationRequest.query.filter_by(status=ApprovalStatus.REJECTED).order_by(
            RegistrationRequest.updated_at.desc()).all()
        title = 'Rejected Registration Requests'
    else:
        requests = RegistrationRequest.query.order_by(RegistrationRequest.created_at.desc()).all()
        title = 'All Registration Requests'
    
    return render_template('admin/registrations.html',
                          requests=requests,
                          current_status=status,
                          title=title)

@bp.route('/registrations/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def review_registration(id):
    """Review and approve/reject a registration request"""
    reg_request = RegistrationRequest.query.get_or_404(id)
    form = RequestReviewForm()
    
    if form.validate_on_submit():
        if form.action.data == 'approve':
            # Approve the request and create the user
            user = reg_request.approve(current_user)
            
            # Send approval email
            send_approval_email(reg_request)
            
            flash(f'Registration request for {reg_request.email} has been approved.', 'success')
        else:
            # Reject the request
            reg_request.reject(current_user, form.rejection_reason.data)
            
            # Send rejection email
            send_rejection_email(reg_request, form.rejection_reason.data)
            
            flash(f'Registration request for {reg_request.email} has been rejected.', 'warning')
            
        return redirect(url_for('admin.registrations'))
    
    return render_template('admin/review_registration.html',
                          request=reg_request,
                          form=form,
                          title='Review Registration Request')

def send_approval_email(request):
    """Send an email to notify user their registration was approved"""
    subject = 'Your Registration Request Has Been Approved'
    body = f"""
    Dear {request.first_name} {request.last_name},
    
    We're pleased to inform you that your registration request has been approved.
    
    You can now log in to the Property Management system using your email ({request.email}) and the password you provided during registration.
    
    Click here to log in: {url_for('auth.login', _external=True)}
    
    Welcome aboard!
    
    Best regards,
    The Property Management Team
    """
    
    send_email(subject, recipients=[request.email], text_body=body, html_body=body)

def send_rejection_email(request, reason):
    """Send an email to notify user their registration was rejected"""
    subject = 'Update on Your Registration Request'
    body = f"""
    Dear {request.first_name} {request.last_name},
    
    We've reviewed your registration request for our Property Management system.
    
    Unfortunately, we are unable to approve your request at this time.
    
    """
    
    if reason:
        body += f"Reason: {reason}\n\n"
    
    body += """
    If you believe this is in error or would like to provide additional information, please contact us.
    
    Best regards,
    The Property Management Team
    """
    
    send_email(subject, recipients=[request.email], text_body=body, html_body=body)

@bp.route('/users')
@login_required
@admin_required
def users():
    """View and manage users"""
    role_filter = request.args.get('role', 'all')
    
    if role_filter != 'all':
        users = User.query.filter_by(role=role_filter).order_by(User.created_at.desc()).all()
    else:
        users = User.query.order_by(User.created_at.desc()).all()
    
    return render_template('admin/users.html',
                          users=users,
                          current_role=role_filter,
                          title='User Management')


@bp.route('/users/<int:user_id>/details')
@login_required
@admin_required
def user_details(user_id):
    """Get detailed user information including notes and actions"""
    user = User.query.get_or_404(user_id)
    notes = user.get_recent_notes(20)
    actions = user.get_recent_actions(20)
    
    return jsonify({
        'user': {
            'id': user.id,
            'email': user.email,
            'full_name': user.get_full_name(),
            'role': user.role,
            'is_active': user.is_active,
            'is_suspended': user.is_suspended,
            'created_at': user.created_at.strftime('%Y-%m-%d %H:%M'),
            'last_login': user.last_login.strftime('%Y-%m-%d %H:%M') if user.last_login else 'Never',
            'failed_login_attempts': user.failed_login_attempts,
            'status': user.status_text,
            'status_badge_class': user.status_badge_class
        },
        'notes': [{
            'id': note.id,
            'content': note.content,
            'note_type': note.note_type,
            'is_important': note.is_important,
            'admin_name': note.admin_name,
            'created_at': note.created_at.strftime('%Y-%m-%d %H:%M')
        } for note in notes],
        'actions': [{
            'id': action.id,
            'action_type': action.action_type,
            'old_value': action.old_value,
            'new_value': action.new_value,
            'reason': action.reason,
            'admin_name': action.admin_name,
            'created_at': action.created_at.strftime('%Y-%m-%d %H:%M')
        } for action in actions]
    })


@bp.route('/users/<int:user_id>/disable', methods=['POST'])
@login_required
@admin_required
def disable_user(user_id):
    """Disable a user account"""
    user = User.query.get_or_404(user_id)
    reason = request.json.get('reason', '') if request.is_json else request.form.get('reason', '')
    
    if user.id == current_user.id:
        return jsonify({'success': False, 'error': 'Cannot disable your own account'}), 400
    
    if user.disable_account(current_user, reason):
        flash(f'User {user.email} has been disabled', 'success')
        return jsonify({'success': True, 'message': f'User {user.email} has been disabled'})
    else:
        return jsonify({'success': False, 'error': 'User is already disabled'}), 400


@bp.route('/users/<int:user_id>/enable', methods=['POST'])
@login_required
@admin_required
def enable_user(user_id):
    """Enable a user account"""
    user = User.query.get_or_404(user_id)
    reason = request.json.get('reason', '') if request.is_json else request.form.get('reason', '')
    
    if user.enable_account(current_user, reason):
        flash(f'User {user.email} has been enabled', 'success')
        return jsonify({'success': True, 'message': f'User {user.email} has been enabled'})
    else:
        return jsonify({'success': False, 'error': 'User is already enabled'}), 400


@bp.route('/users/<int:user_id>/change-role', methods=['POST'])
@login_required
@admin_required
def change_user_role(user_id):
    """Change a user's role and handle assignments"""
    from app.models import PropertyAssignment, UserManagerAssignment, UserOwnerAssignment
    
    user = User.query.get_or_404(user_id)
    new_role = request.json.get('role') if request.is_json else request.form.get('role')
    reason = request.json.get('reason', '') if request.is_json else request.form.get('reason', '')
    assignments = request.json.get('assignments', {}) if request.is_json else {}
    
    if user.id == current_user.id:
        return jsonify({'success': False, 'error': 'Cannot change your own role'}), 400
    
    # Validate role
    try:
        UserRoles(new_role)
    except ValueError:
        return jsonify({'success': False, 'error': 'Invalid role specified'}), 400
    
    # Change the role first
    if user.change_role(new_role, current_user, reason):
        # Handle assignments based on the new role
        try:
            # Clear existing assignments for this user
            PropertyAssignment.query.filter_by(user_id=user.id, is_active=True).update({'is_active': False})
            UserManagerAssignment.query.filter_by(user_id=user.id, is_active=True).update({'is_active': False})
            UserOwnerAssignment.query.filter_by(manager_id=user.id, is_active=True).update({'is_active': False})
            
            assignment_messages = []
            
            # Property assignments for property managers and service staff
            if new_role in ['property_manager', 'service_staff'] and assignments.get('properties'):
                for property_id in assignments['properties']:
                    assignment = PropertyAssignment(
                        user_id=user.id,
                        property_id=int(property_id),
                        assigned_by=current_user.id,
                        role=new_role,
                        is_active=True
                    )
                    db.session.add(assignment)
                assignment_messages.append(f"Assigned to {len(assignments['properties'])} properties")
            
            # Manager assignment for service staff
            if new_role == 'service_staff' and assignments.get('manager'):
                assignment = UserManagerAssignment(
                    user_id=user.id,
                    manager_id=int(assignments['manager']),
                    assigned_by=current_user.id,
                    is_active=True
                )
                db.session.add(assignment)
                assignment_messages.append("Assigned to property manager")
            
            # Owner assignment for property managers
            if new_role == 'property_manager' and assignments.get('owner'):
                assignment = UserOwnerAssignment(
                    manager_id=user.id,
                    owner_id=int(assignments['owner']),
                    assigned_by=current_user.id,
                    is_active=True
                )
                db.session.add(assignment)
                assignment_messages.append("Assigned to property owner")
            
            db.session.commit()
            
            success_message = f'User {user.email} role changed to {new_role}'
            if assignment_messages:
                success_message += f'. {", ".join(assignment_messages)}'
            
            flash(success_message, 'success')
            return jsonify({'success': True, 'message': success_message})
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'error': f'Assignment failed: {str(e)}'}), 400
    else:
        return jsonify({'success': False, 'error': 'Role change failed'}), 400


@bp.route('/users/<int:user_id>/reset-password', methods=['POST'])
@login_required
@admin_required
def reset_user_password(user_id):
    """Reset a user's password"""
    user = User.query.get_or_404(user_id)
    reason = request.json.get('reason', '') if request.is_json else request.form.get('reason', '')
    send_email_notification = request.json.get('send_email', True) if request.is_json else request.form.get('send_email', 'true') == 'true'
    
    # Generate random password
    def generate_random_password(length=12):
        characters = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(secrets.choice(characters) for _ in range(length))
    
    new_password = generate_random_password()
    
    if user.reset_password_admin(current_user, new_password, reason):
        if send_email_notification:
            # Send email with new password
            subject = 'Your Password Has Been Reset'
            body = f"""
            Dear {user.get_full_name()},
            
            Your password has been reset by an administrator.
            
            Your new temporary password is: {new_password}
            
            Please log in and change your password immediately.
            
            Login here: {url_for('auth.login', _external=True)}
            
            Best regards,
            The Property Management Team
            """
            send_email(subject, recipients=[user.email], text_body=body, html_body=body)
        
        flash(f'Password reset for {user.email}', 'success')
        return jsonify({
            'success': True, 
            'message': f'Password reset for {user.email}',
            'new_password': new_password if not send_email_notification else None
        })
    else:
        return jsonify({'success': False, 'error': 'Password reset failed'}), 400


@bp.route('/users/<int:user_id>/add-note', methods=['POST'])
@login_required
@admin_required
def add_user_note(user_id):
    """Add a note to a user"""
    user = User.query.get_or_404(user_id)
    content = request.json.get('content') if request.is_json else request.form.get('content')
    note_type = request.json.get('note_type', 'general') if request.is_json else request.form.get('note_type', 'general')
    is_important = request.json.get('is_important', False) if request.is_json else request.form.get('is_important') == 'true'
    
    if not content or not content.strip():
        return jsonify({'success': False, 'error': 'Note content is required'}), 400
    
    note = user.add_admin_note(current_user, content.strip(), note_type, is_important)
    
    return jsonify({
        'success': True,
        'message': 'Note added successfully',
        'note': {
            'id': note.id,
            'content': note.content,
            'note_type': note.note_type,
            'is_important': note.is_important,
            'admin_name': note.admin_name,
            'created_at': note.created_at.strftime('%Y-%m-%d %H:%M')
        }
    })


@bp.route('/users/<int:user_id>/notes/<int:note_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user_note(user_id, note_id):
    """Delete a user note"""
    note = UserNote.query.get_or_404(note_id)
    
    if note.user_id != user_id:
        return jsonify({'success': False, 'error': 'Note does not belong to this user'}), 400
    
    # Only allow deletion by the admin who created the note or super admin
    if note.admin_id != current_user.id and not current_user.is_admin:
        return jsonify({'success': False, 'error': 'You can only delete your own notes'}), 403
    
    db.session.delete(note)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Note deleted successfully'})


@bp.route('/user-roles')
@login_required
@admin_required
def get_user_roles():
    """Get available user roles for dropdowns"""
    roles = [{'value': role.value, 'name': role.value.replace('_', ' ').title()} for role in UserRoles]
    return jsonify({'roles': roles})


@bp.route('/properties-list')
@login_required
@admin_required
def get_properties_list():
    """Get list of all properties for assignment dropdowns"""
    from app.models import Property
    properties = Property.query.all()
    properties_data = []
    for prop in properties:
        properties_data.append({
            'id': prop.id,
            'name': prop.name or f"Property #{prop.id}",
            'address': prop.address or "No address"
        })
    return jsonify({'properties': properties_data})


@bp.route('/property-managers')
@login_required
@admin_required
def get_property_managers():
    """Get list of property managers for assignment dropdowns"""
    managers = User.query.filter_by(role=UserRoles.PROPERTY_MANAGER.value).all()
    managers_data = []
    for manager in managers:
        managers_data.append({
            'id': manager.id,
            'name': manager.get_full_name(),
            'email': manager.email
        })
    return jsonify({'managers': managers_data})


@bp.route('/property-owners')
@login_required
@admin_required
def get_property_owners():
    """Get list of property owners for assignment dropdowns"""
    owners = User.query.filter_by(role=UserRoles.PROPERTY_OWNER.value).all()
    owners_data = []
    for owner in owners:
        owners_data.append({
            'id': owner.id,
            'name': owner.get_full_name(),
            'email': owner.email
        })
    return jsonify({'owners': owners_data}) 