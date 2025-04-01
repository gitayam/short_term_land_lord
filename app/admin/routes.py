from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.admin import bp
from app.models import SiteSettings, User, UserRoles, RepairRequest, RepairRequestStatus, Property
from app.admin.forms import SiteSettingsForm
from app.auth.decorators import admin_required

@bp.route('/settings', methods=['GET', 'POST'])
@login_required
@admin_required
def settings():
    """Manage site settings"""
    form = SiteSettingsForm()
    
    if form.validate_on_submit():
        # Save OpenAI API key
        SiteSettings.set_setting('openai_api_key', form.openai_api_key.data, 'OpenAI API Key for AI functionality', False)
        
        # Save guest reviews enabled setting
        SiteSettings.set_setting('guest_reviews_enabled', str(form.enable_guest_reviews.data).lower(), 'Enable guest reviews feature', True)
        
        flash('Settings saved successfully!', 'success')
        return redirect(url_for('admin.settings'))
    
    elif request.method == 'GET':
        # Pre-fill form with current settings
        openai_api_key = SiteSettings.get_setting('openai_api_key')
        if openai_api_key:
            form.openai_api_key.data = openai_api_key
        
        guest_reviews_enabled = SiteSettings.get_setting('guest_reviews_enabled')
        if guest_reviews_enabled:
            form.enable_guest_reviews.data = guest_reviews_enabled.lower() == 'true'
    
    # Get list of public settings for display
    public_settings = SiteSettings.query.filter_by(visible=True).all()
    
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
    owner_count = User.query.filter(User.roles.contains(UserRoles.PROPERTY_OWNER)).count()
    manager_count = User.query.filter(User.roles.contains(UserRoles.PROPERTY_MANAGER)).count()
    staff_count = User.query.filter(User.roles.contains(UserRoles.SERVICE_STAFF)).count()
    
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
                          pending_requests=pending_requests,
                          property_dict=property_dict,
                          title='Admin Dashboard') 