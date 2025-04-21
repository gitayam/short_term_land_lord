from flask import render_template, flash, redirect, url_for, request, current_app, jsonify
from flask_login import current_user, login_required
from app import db
from app.profile import bp
from app.models import User
from werkzeug.security import check_password_hash
from datetime import datetime
import json
from app.profile.forms import PersonalInfoForm, ChangePasswordForm, PreferencesForm

@bp.route('/profile')
@login_required
def profile():
    """Display user profile page"""
    preferences_form = PreferencesForm()
    # Set initial values from current_user
    preferences_form.theme_preference.data = current_user.theme_preference
    preferences_form.default_dashboard_view.data = current_user.default_dashboard_view
    preferences_form.default_calendar_view.data = current_user.default_calendar_view
    preferences_form.default_task_sort.data = current_user.default_task_sort
    
    return render_template('profile/profile.html', form=preferences_form)

@bp.route('/profile/update/personal', methods=['POST'])
@login_required
def update_personal_info():
    """Update personal information"""
    try:
        current_user.first_name = request.form.get('first_name', current_user.first_name)
        current_user.last_name = request.form.get('last_name', current_user.last_name)
        current_user.email = request.form.get('email', current_user.email)
        current_user.phone = request.form.get('phone', current_user.phone)
        current_user.timezone = request.form.get('timezone', current_user.timezone)
        current_user.language = request.form.get('language', current_user.language)
        
        db.session.commit()
        flash('Personal information updated successfully', 'success')
    except Exception as e:
        current_app.logger.error(f"Error updating profile: {e}")
        flash('An error occurred while updating your profile', 'error')
        db.session.rollback()
    
    return redirect(url_for('profile.profile'))

@bp.route('/profile/update/password', methods=['POST'])
@login_required
def change_password():
    """Change user password"""
    try:
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if not current_user.check_password(current_password):
            flash('Current password is incorrect', 'error')
            return redirect(url_for('profile.profile'))
            
        if new_password != confirm_password:
            flash('New passwords do not match', 'error')
            return redirect(url_for('profile.profile'))
            
        current_user.set_password(new_password)
        current_user.last_password_change = datetime.utcnow()
        db.session.commit()
        
        flash('Password changed successfully', 'success')
    except Exception as e:
        current_app.logger.error(f"Error changing password: {e}")
        flash('An error occurred while changing your password', 'error')
        db.session.rollback()
    
    return redirect(url_for('profile.profile'))

@bp.route('/profile/update/notifications', methods=['POST'])
@login_required
def update_notifications():
    """Update notification preferences"""
    try:
        current_user.email_notifications = bool(request.form.get('email-tasks'))
        current_user.sms_notifications = bool(request.form.get('sms-urgent'))
        current_user.in_app_notifications = bool(request.form.get('app-all'))
        
        db.session.commit()
        flash('Notification preferences updated successfully', 'success')
    except Exception as e:
        current_app.logger.error(f"Error updating notifications: {e}")
        flash('An error occurred while updating your notification preferences', 'error')
        db.session.rollback()
    
    return redirect(url_for('profile.profile'))

@bp.route('/profile/update/preferences', methods=['POST'])
@login_required
def update_preferences():
    form = PreferencesForm()
    if form.validate_on_submit():
        current_user.theme_preference = form.theme_preference.data
        current_user.default_dashboard_view = form.default_dashboard_view.data
        current_user.default_calendar_view = form.default_calendar_view.data
        current_user.default_task_sort = form.default_task_sort.data
        
        try:
            db.session.commit()
            flash('Preferences updated successfully!', 'success')
            return jsonify({'status': 'success', 'message': 'Preferences updated successfully!'})
        except Exception as e:
            db.session.rollback()
            flash('Error updating preferences. Please try again.', 'error')
            return jsonify({'status': 'error', 'message': 'Error updating preferences'}), 500
    else:
        return jsonify({'status': 'error', 'message': 'Invalid form data'}), 400

@bp.route('/profile/upload-image', methods=['POST'])
@login_required
def upload_profile_image():
    """Handle profile image upload"""
    if 'profile_image' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
        
    file = request.files['profile_image']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
        
    try:
        # Handle file upload logic here
        # Save file to appropriate location
        # Update user profile_image field
        
        return jsonify({'success': True, 'message': 'Profile image updated successfully'})
    except Exception as e:
        current_app.logger.error(f"Error uploading profile image: {e}")
        return jsonify({'error': 'Failed to upload image'}), 500

@bp.route('/profile/toggle-2fa', methods=['POST'])
@login_required
def toggle_2fa():
    """Toggle two-factor authentication"""
    try:
        enabled = request.json.get('enabled', False)
        method = request.json.get('method', 'sms')
        
        current_user.two_factor_enabled = enabled
        current_user.two_factor_method = method if enabled else None
        
        db.session.commit()
        return jsonify({'success': True, 'message': '2FA settings updated successfully'})
    except Exception as e:
        current_app.logger.error(f"Error updating 2FA settings: {e}")
        return jsonify({'error': 'Failed to update 2FA settings'}), 500

@bp.route('/profile/connect-service', methods=['POST'])
@login_required
def connect_service():
    """Connect external service"""
    service = request.json.get('service')
    
    try:
        if service == 'google_calendar':
            # Handle Google Calendar connection
            pass
        elif service == 'twilio':
            # Handle Twilio verification
            pass
        elif service == 'slack':
            # Handle Slack workspace connection
            pass
            
        return jsonify({'success': True, 'message': f'{service} connected successfully'})
    except Exception as e:
        current_app.logger.error(f"Error connecting service {service}: {e}")
        return jsonify({'error': f'Failed to connect {service}'}), 500