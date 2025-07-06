from flask import render_template, request, jsonify, current_app, flash, redirect, url_for
from flask_login import login_required, current_user
from app.messages import bp
from app.utils.sms import handle_incoming_sms, handle_status_callback, send_sms, format_phone_number
from app.models import MessageThread, Message, User, Task, TaskAssignment, TaskStatus, Notification
from app import db
from datetime import datetime
import logging
from app.messages.service import get_unified_messages

logger = logging.getLogger(__name__)

@bp.route('/webhook', methods=['POST'])
def webhook():
    """Handle incoming SMS webhook from Twilio"""
    try:
        # Verify this is a legitimate Twilio request (basic validation)
        # In production, you should verify the request signature
        return handle_incoming_sms()
    except Exception as e:
        current_app.logger.error(f"Error in SMS webhook: {str(e)}")
        # Return empty TwiML response to avoid Twilio errors
        from twilio.twiml.messaging_response import MessagingResponse
        return str(MessagingResponse())

@bp.route('/status-callback', methods=['POST'])
def status_callback():
    """Handle SMS status callback from Twilio"""
    try:
        return handle_status_callback()
    except Exception as e:
        current_app.logger.error(f"Error in status callback: {str(e)}")
        return '', 500

@bp.route('/threads')
@login_required
def threads():
    """Display all message threads for the current user"""
    try:
        all_messages = get_unified_messages(current_user)
        return render_template('messages/threads.html',
                              title='Messages',
                              messages=all_messages,
                              user=current_user)
    except Exception as e:
        current_app.logger.error(f"Error loading messages threads: {str(e)}")
        flash('Error loading messages', 'error')
        return render_template('messages/threads.html',
                              title='Messages',
                              messages=[],
                              user=current_user)

@bp.route('/view/<msg_type>/<int:msg_id>', methods=['GET', 'POST'])
@login_required
def view_message(msg_type, msg_id):
    """Display the detail view for a message (SMS thread, notification, etc.)"""
    if msg_type == 'sms':
        # Find the message and thread
        msg = Message.query.get_or_404(msg_id)
        thread = MessageThread.query.get_or_404(msg.thread_id)
        # Only allow access if user is participant
        if not (thread.user_id == current_user.id or thread.participant_phone == current_user.phone):
            flash('You do not have access to this conversation', 'error')
            return redirect(url_for('messages.threads'))
        # Get all messages in thread
        messages = thread.messages.order_by(Message.created_at.asc()).all()
        # Handle reply
        if request.method == 'POST':
            content = request.form.get('reply')
            if content:
                success, error = send_sms(thread.participant_phone, content, thread_id=thread.id)
                if success:
                    flash('Reply sent successfully', 'success')
                    return redirect(url_for('messages.view_message', msg_type='sms', msg_id=msg_id))
                else:
                    flash(f'Failed to send reply: {error}', 'error')
        return render_template('messages/view_thread.html', thread=thread, messages=messages, msg_type='sms')
    elif msg_type == 'notification':
        notification = Notification.query.get_or_404(msg_id)
        if notification.recipient_id != current_user.id:
            flash('You do not have access to this notification', 'error')
            return redirect(url_for('messages.threads'))
        return render_template('messages/view_thread.html', notification=notification, msg_type='notification')
    else:
        flash('Unknown message type', 'error')
        return redirect(url_for('messages.threads'))

@bp.route('/thread/<int:thread_id>')
@login_required
def view_thread(thread_id):
    """View a specific message thread"""
    try:
        thread = MessageThread.query.get_or_404(thread_id)
        
        # Check if user has access to this thread
        if (thread.participant_phone != current_user.phone and 
            thread.user_id != current_user.id):
            flash('You do not have access to this conversation', 'error')
            return redirect(url_for('messages.threads'))
        
        # Mark messages as read
        thread.mark_all_read()
        
        # Get messages ordered by creation time
        messages = thread.messages.order_by(Message.created_at.asc()).all()
        
        return render_template('messages/view_thread.html',
                             title=f'Message Conversation with {thread.participant_phone}',
                             thread=thread,
                             messages=messages)
    except Exception as e:
        current_app.logger.error(f"Error viewing message thread: {str(e)}")
        flash('Error loading conversation', 'error')
        return redirect(url_for('messages.threads'))

@bp.route('/thread/<int:thread_id>/send', methods=['POST'])
@login_required
def send_message(thread_id):
    """Send a message in a thread"""
    try:
        thread = MessageThread.query.get_or_404(thread_id)
        
        # Check if user has access to this thread
        if (thread.participant_phone != current_user.phone and 
            thread.user_id != current_user.id):
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        message_content = request.form.get('message', '').strip()
        if not message_content:
            return jsonify({'success': False, 'error': 'Message cannot be empty'}), 400
        
        # Send SMS
        success, error = send_sms(
            to_number=thread.participant_phone,
            message=message_content,
            thread_id=thread.id
        )
        
        if success:
            # Update thread timestamp
            thread.updated_at = datetime.utcnow()
            db.session.commit()
            
            return jsonify({'success': True, 'message': 'Message sent successfully'})
        else:
            return jsonify({'success': False, 'error': error}), 500
            
    except Exception as e:
        current_app.logger.error(f"Error sending message: {str(e)}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@bp.route('/send_to_user/<int:user_id>', methods=['GET', 'POST'])
@login_required
def send_to_user(user_id):
    """Send message to a specific user"""
    try:
        user = User.query.get_or_404(user_id)
        
        if not user.phone:
            flash('This user does not have a phone number registered', 'error')
            return redirect(url_for('main.index'))
        
        if request.method == 'POST':
            message_content = request.form.get('message', '').strip()
            if not message_content:
                flash('Message cannot be empty', 'error')
                return redirect(url_for('messages.send_to_user', user_id=user_id))
            
            # Find or create thread
            thread = MessageThread.query.filter_by(
                participant_phone=user.phone,
                system_phone=current_app.config.get('TWILIO_PHONE_NUMBER')
            ).first()
            
            if not thread:
                thread = MessageThread(
                    participant_phone=user.phone,
                    system_phone=current_app.config.get('TWILIO_PHONE_NUMBER'),
                    user_id=user.id
                )
                db.session.add(thread)
                db.session.commit()
            
            # Send SMS
            success, error = send_sms(
                to_number=user.phone,
                message=message_content,
                thread_id=thread.id
            )
            
            if success:
                flash('Message sent successfully', 'success')
                return redirect(url_for('messages.view_thread', thread_id=thread.id))
            else:
                flash(f'Failed to send message: {error}', 'error')
        
        return render_template('messages/send_to_user.html',
                             title=f'Send Message to {user.get_full_name()}',
                             user=user)
    except Exception as e:
        current_app.logger.error(f"Error sending message to user: {str(e)}")
        flash('Error sending message', 'error')
        return redirect(url_for('main.index'))

@bp.route('/api/threads')
@login_required
def api_threads():
    """API endpoint to get user's message threads"""
    try:
        threads = MessageThread.query.filter_by(
            participant_phone=current_user.phone
        ).order_by(MessageThread.updated_at.desc()).all()
        
        thread_data = []
        for thread in threads:
            last_message = thread.last_message
            thread_data.append({
                'id': thread.id,
                'participant_phone': thread.participant_phone,
                'unread_count': thread.unread_count,
                'last_message': {
                    'content': last_message.content[:100] + '...' if last_message and len(last_message.content) > 100 else last_message.content if last_message else '',
                    'direction': last_message.direction if last_message else None,
                    'created_at': last_message.created_at.isoformat() if last_message else None
                } if last_message else None,
                'updated_at': thread.updated_at.isoformat()
            })
        
        return jsonify({'success': True, 'threads': thread_data})
    except Exception as e:
        current_app.logger.error(f"Error in API threads: {str(e)}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@bp.route('/api/thread/<int:thread_id>/messages')
@login_required
def api_thread_messages(thread_id):
    """API endpoint to get messages in a thread"""
    try:
        thread = MessageThread.query.get_or_404(thread_id)
        
        # Check access
        if (thread.participant_phone != current_user.phone and 
            thread.user_id != current_user.id):
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        messages = thread.messages.order_by(Message.created_at.asc()).all()
        
        message_data = []
        for message in messages:
            message_data.append({
                'id': message.id,
                'direction': message.direction,
                'content': message.content,
                'status': message.status,
                'read': message.read,
                'created_at': message.created_at.isoformat()
            })
        
        return jsonify({'success': True, 'messages': message_data})
    except Exception as e:
        current_app.logger.error(f"Error in API thread messages: {str(e)}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@bp.route('/api/mark-read/<int:message_id>', methods=['POST'])
@login_required
def api_mark_read(message_id):
    """API endpoint to mark a message as read"""
    try:
        message = Message.query.get_or_404(message_id)
        
        # Check access through thread
        thread = message.thread
        if (thread.participant_phone != current_user.phone and 
            thread.user_id != current_user.id):
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        message.mark_read()
        
        return jsonify({'success': True})
    except Exception as e:
        current_app.logger.error(f"Error marking message as read: {str(e)}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@bp.route('/new', methods=['GET', 'POST'])
@login_required
def new_message():
    from app.models import User
    from app.utils.sms import send_sms
    # Only allow sending to workforce (service staff)
    workforce = User.query.filter_by(role='service_staff').all()
    if request.method == 'POST':
        recipient_id = request.form.get('recipient_id')
        content = request.form.get('content')
        recipient = User.query.get_or_404(recipient_id)
        if not content:
            flash('Message cannot be empty', 'error')
            return render_template('messages/new_message.html', workforce=workforce)
        # Save as a direct message (in-app)
        # For now, use MessageThread/Message with a special type or tag
        from app.models import MessageThread, Message
        # Find or create a thread
        thread = MessageThread.query.filter_by(user_id=recipient.id, participant_phone=recipient.phone).first()
        if not thread:
            thread = MessageThread(user_id=recipient.id, participant_phone=recipient.phone, system_phone=current_app.config.get('TWILIO_PHONE_NUMBER', ''), status='active')
            db.session.add(thread)
            db.session.commit()
        # Create the message
        msg = Message(thread_id=thread.id, direction='outgoing', phone_number=recipient.phone, content=content, status='sent', read=False)
        db.session.add(msg)
        db.session.commit()
        # Relay via SMS
        success, error = send_sms(recipient.phone, content, thread_id=thread.id)
        if success:
            flash('Message sent and relayed via SMS', 'success')
        else:
            flash(f'Message saved, but SMS relay failed: {error}', 'warning')
        return redirect(url_for('messages.view_message', msg_type='sms', msg_id=msg.id))
    return render_template('messages/new_message.html', workforce=workforce) 