from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.notifications import bp
from app.models import Notification

@bp.route('/')
@login_required
def index():
    """View all notifications for the current user"""
    notifications = Notification.query.filter_by(
        user_id=current_user.id
    ).order_by(Notification.sent_at.desc()).all()

    # Count unread notifications
    unread_count = Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).count()

    return render_template('notifications/index.html',
                          title='Notifications',
                          notifications=notifications,
                          unread_count=unread_count)

@bp.route('/<int:id>/mark_read', methods=['POST'])
@login_required
def mark_read(id):
    """Mark a notification as read"""
    notification = Notification.query.get_or_404(id)

    # Check if notification belongs to current user
    if notification.user_id != current_user.id:
        flash('You do not have permission to access this notification.', 'danger')
        return redirect(url_for('notifications.index'))

    notification.mark_as_read()
    db.session.commit()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True})

    flash('Notification marked as read.', 'success')
    return redirect(url_for('notifications.index'))

@bp.route('/mark_all_read', methods=['POST'])
@login_required
def mark_all_read():
    """Mark all notifications as read"""
    notifications = Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).all()

    for notification in notifications:
        notification.mark_as_read()

    db.session.commit()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True})

    flash('All notifications marked as read.', 'success')
    return redirect(url_for('notifications.index'))
