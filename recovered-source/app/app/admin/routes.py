from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import SiteSetting, User, UserRoles, RepairRequest, RepairRequestStatus, Property, RegistrationRequest, ApprovalStatus
from app.admin.forms import SiteSettingsForm, RequestReviewForm
from app.auth.decorators import admin_required
from app.auth.email import send_email

bp = Blueprint('admin', __name__)

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
            RepairRequestStatus.PENDING.value, 
            RepairRequestStatus.APPROVED.value
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