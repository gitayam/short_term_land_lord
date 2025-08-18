from flask import render_template, flash, redirect, url_for, request, current_app, jsonify
from flask_login import current_user, login_required
from app import db
from app.profile import bp
from app.models import User
from werkzeug.security import check_password_hash
from datetime import datetime
import json
from app.profile.forms import PersonalInfoForm, ChangePasswordForm, PreferencesForm

@bp.route('/')
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

@bp.route('/update/personal', methods=['POST'])
@login_required
def update_personal_info():
    """Update personal information"""
    try:
        current_app.logger.info(f"Personal info update requested by user {current_user.email}")
        current_app.logger.info(f"Form data: {dict(request.form)}")
        
        # Get actual user object from database instead of using current_user proxy
        user = User.query.get(current_user.id)
        current_app.logger.info(f"Before update - Name: {user.first_name} {user.last_name}")
        
        user.first_name = request.form.get('first_name', user.first_name)
        user.last_name = request.form.get('last_name', user.last_name)
        user.email = request.form.get('email', user.email)
        user.phone = request.form.get('phone', user.phone)
        user.timezone = request.form.get('timezone', user.timezone)
        user.language = request.form.get('language', user.language)
        
        current_app.logger.info(f"After assignment - Name: {user.first_name} {user.last_name}")
        
        db.session.add(user)  # Explicitly add to session
        db.session.commit()
        
        # Verify the commit worked
        user_check = User.query.get(user.id)
        current_app.logger.info(f"Post-commit verification - Name: {user_check.first_name} {user_check.last_name}")
        
        flash('Personal information updated successfully', 'success')
    except Exception as e:
        current_app.logger.error(f"Error updating profile: {e}")
        flash('An error occurred while updating your profile', 'error')
        db.session.rollback()
    
    return redirect(url_for('profile.profile'))

@bp.route('/update/password', methods=['POST'])
@login_required
def change_password():
    """Change user password"""
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    if not current_user.check_password(current_password):
        flash('Current password is incorrect', 'error')
        return redirect(url_for('profile.profile'))
    
    if new_password != confirm_password:
        flash('New passwords do not match', 'error')
        return redirect(url_for('profile.profile'))
    
    if len(new_password) < 6:
        flash('Password must be at least 6 characters long', 'error')
        return redirect(url_for('profile.profile'))
    
    try:
        # Get actual user object from database
        user = User.query.get(current_user.id)
        user.set_password(new_password)
        user.last_password_change = datetime.utcnow()
        
        db.session.add(user)
        db.session.commit()
        flash('Password changed successfully', 'success')
    except Exception as e:
        current_app.logger.error(f"Error changing password: {e}")
        flash('An error occurred while changing your password', 'error')
        db.session.rollback()
    
    return redirect(url_for('profile.profile'))

@bp.route('/update/notifications', methods=['POST'])
@login_required
def update_notifications():
    """Update notification preferences"""
    try:
        # Get actual user object from database
        user = User.query.get(current_user.id)
        user.email_notifications = bool(request.form.get('email-tasks'))
        user.sms_notifications = bool(request.form.get('sms-urgent'))
        user.in_app_notifications = bool(request.form.get('app-all'))
        
        db.session.add(user)
        db.session.commit()
        flash('Notification preferences updated successfully', 'success')
    except Exception as e:
        current_app.logger.error(f"Error updating notifications: {e}")
        flash('An error occurred while updating your notification preferences', 'error')
        db.session.rollback()
    
    return redirect(url_for('profile.profile'))

@bp.route('/update/preferences', methods=['POST'])
@login_required
def update_preferences():
    form = PreferencesForm()
    current_app.logger.info(f"Form data received: {request.form}")
    current_app.logger.info(f"Form validation result: {form.validate_on_submit()}")
    
    if form.validate_on_submit():
        current_app.logger.info(f"Updating preferences - Theme: {form.theme_preference.data}, Dashboard: {form.default_dashboard_view.data}")
        
        # Get the actual user object from database instead of using current_user proxy
        user = User.query.get(current_user.id)
        current_app.logger.info(f"Before update - User theme in DB: {user.theme_preference}")
        
        user.theme_preference = form.theme_preference.data
        user.default_dashboard_view = form.default_dashboard_view.data
        user.default_calendar_view = form.default_calendar_view.data
        user.default_task_sort = form.default_task_sort.data
        
        current_app.logger.info(f"After assignment - User theme: {user.theme_preference}")
        
        try:
            db.session.add(user)  # Explicitly add to session
            db.session.commit()
            current_app.logger.info(f"Preferences committed successfully for user {user.email}")
            
            # Verify the commit worked
            user_check = User.query.get(user.id)
            current_app.logger.info(f"Post-commit verification - User theme: {user_check.theme_preference}")
            
            flash('Preferences updated successfully!', 'success')
            return jsonify({
                'status': 'success', 
                'message': 'Preferences updated successfully!',
                'theme': user.theme_preference
            })
        except Exception as e:
            current_app.logger.error(f"Error updating preferences: {e}")
            db.session.rollback()
            flash('Error updating preferences. Please try again.', 'error')
            return jsonify({'status': 'error', 'message': 'Error updating preferences'}), 500
    else:
        current_app.logger.error(f"Form validation failed. Errors: {form.errors}")
        return jsonify({'status': 'error', 'message': f'Invalid form data: {form.errors}'}), 400

@bp.route('/upload-image', methods=['POST'])
@login_required
def upload_profile_image():
    """Handle profile image upload"""
    if 'profile_image' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['profile_image']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
        try:
            # Save file logic would go here
            current_user.profile_image = f"uploads/profile/{file.filename}"
            db.session.commit()
            return jsonify({'success': True, 'message': 'Profile image updated successfully'})
        except Exception as e:
            current_app.logger.error(f"Error uploading profile image: {e}")
            return jsonify({'error': 'Failed to upload image'}), 500
    
    return jsonify({'error': 'Invalid file type'}), 400

@bp.route('/toggle-2fa', methods=['POST'])
@login_required
def toggle_2fa():
    """Toggle two-factor authentication"""
    try:
        enabled = request.json.get('enabled', False)
        method = request.json.get('method', 'sms')
    except AttributeError as e:
        current_app.logger.error(f"Failed to access request.json in toggle_2fa: {e}", exc_info=True)
        flash("This feature isn't available right now. Please try again later.", "danger")
        return redirect(url_for('profile.profile'))
    
    try:
        current_user.two_factor_enabled = enabled
        current_user.two_factor_method = method if enabled else None
        
        db.session.commit()
        return jsonify({'success': True, 'message': '2FA settings updated successfully'})
    except Exception as e:
        current_app.logger.error(f"Error updating 2FA settings: {e}")
        return jsonify({'error': 'Failed to update 2FA settings'}), 500

@bp.route('/connect-service', methods=['POST'])
@login_required
def connect_service():
    """Connect or disconnect external services"""
    service = request.form.get('service')
    
    if service == 'google_calendar':
        # Toggle Google Calendar connection
        current_user.google_calendar_connected = not current_user.google_calendar_connected
        if not current_user.google_calendar_connected:
            current_user.google_calendar_token = None
        
        try:
            db.session.commit()
            status = 'connected' if current_user.google_calendar_connected else 'disconnected'
            flash(f'Google Calendar {status} successfully', 'success')
        except Exception as e:
            current_app.logger.error(f"Error updating Google Calendar connection: {e}")
            flash('An error occurred while updating Google Calendar connection', 'error')
            db.session.rollback()
    
    elif service == 'slack':
        # Toggle Slack connection
        if current_user.slack_workspace_id:
            current_user.slack_workspace_id = None
            status = 'disconnected'
        else:
            current_user.slack_workspace_id = 'demo_workspace'
            status = 'connected'
        
        try:
            db.session.commit()
            flash(f'Slack {status} successfully', 'success')
        except Exception as e:
            current_app.logger.error(f"Error updating Slack connection: {e}")
            flash('An error occurred while updating Slack connection', 'error')
            db.session.rollback()
    
    return redirect(url_for('profile.profile'))