from flask import current_app, render_template
from app import db
from app.models import Notification, NotificationType, NotificationChannel, User, Task, Property, MessageThread, Message
from app.common.email import send_email
from app.utils.sms import send_sms, format_phone_number
from datetime import datetime, timedelta
import requests
import logging

def send_task_assignment_notification(task, user):
    """Send notification when a task is assigned to a user"""
    if not user or not task:
        current_app.logger.error("Cannot send notification: missing user or task")
        return False
    
    # Get property information for the task
    properties = task.properties
    
    property_names = ", ".join([p.name for p in properties])
    
    # Create notification content
    title = f"New Task Assignment: {task.title}"
    message = f"You have been assigned a new task: {task.title}\n"
    message += f"Due date: {task.due_date.strftime('%Y-%m-%d %H:%M') if task.due_date else 'No due date'}\n"
    message += f"Priority: {task.priority.value.capitalize()}\n"
    message += f"Property: {property_names}\n\n"
    message += f"Description: {task.description or 'No description provided'}"
    
    # Create in-app notification
    create_notification(
        user_id=user.id,
        task_id=task.id,
        notification_type=NotificationType.TASK_ASSIGNMENT,
        channel=NotificationChannel.IN_APP,
        title=title,
        message=message
    )
    
    # Send email notification if user preference is enabled
    if getattr(user, 'email_notifications', True) and current_app.config.get('NOTIFICATION_EMAIL_ENABLED', True):
        send_email_notification(
            user=user,
            subject=title,
            text_body=message,
            html_body=render_template('email/task_assignment.html', 
                                     user=user, 
                                     task=task,
                                     properties=properties)
        )
    
    # Send SMS notification if user preference is enabled and user has a phone number
    if getattr(user, 'sms_notifications', False) and current_app.config.get('NOTIFICATION_SMS_ENABLED', True) and getattr(user, 'phone', None):
        # Find or create message thread for SMS
        thread = get_or_create_sms_thread(user.phone)
        
        sms_message = f"New task assigned: {task.title}. Due: {task.due_date.strftime('%Y-%m-%d') if task.due_date else 'No due date'}. Priority: {task.priority.value.capitalize()}."
        
        send_sms_notification(
            phone_number=user.phone,
            message=sms_message,
            thread_id=thread.id if thread else None
        )
    
    return True

def send_task_reminder_notification(task, user):
    """Send reminder notification for upcoming tasks"""
    if not user or not task:
        current_app.logger.error("Cannot send reminder: missing user or task")
        return False
    
    # Get property information for the task
    properties = task.properties
    
    property_names = ", ".join([p.name for p in properties])
    
    # Create notification content
    title = f"Reminder: Task Due Soon - {task.title}"
    message = f"Reminder: Your task '{task.title}' is due soon.\n"
    message += f"Due date: {task.due_date.strftime('%Y-%m-%d %H:%M') if task.due_date else 'No due date'}\n"
    message += f"Priority: {task.priority.value.capitalize()}\n"
    message += f"Property: {property_names}\n\n"
    message += f"Description: {task.description or 'No description provided'}"
    
    # Create in-app notification
    create_notification(
        user_id=user.id,
        task_id=task.id,
        notification_type=NotificationType.TASK_REMINDER,
        channel=NotificationChannel.IN_APP,
        title=title,
        message=message
    )
    
    # Send email notification if enabled
    if current_app.config.get('NOTIFICATION_EMAIL_ENABLED', True):
        send_email_notification(
            user=user,
            subject=title,
            text_body=message,
            html_body=render_template('email/task_reminder.html', 
                                     user=user, 
                                     task=task,
                                     properties=properties)
        )
    
    # Send SMS notification if enabled and user has a phone number
    if current_app.config.get('NOTIFICATION_SMS_ENABLED', True) and hasattr(user, 'phone') and user.phone:
        thread = get_or_create_sms_thread(user.phone)
        
        sms_message = f"Reminder: Task '{task.title}' is due soon. Due: {task.due_date.strftime('%Y-%m-%d') if task.due_date else 'No due date'}."
        
        send_sms_notification(
            phone_number=user.phone,
            message=sms_message,
            thread_id=thread.id if thread else None
        )
    
    return True

def send_calendar_update_notification(task, user):
    """Send notification when a calendar event affecting a task is updated"""
    if not user or not task:
        current_app.logger.error("Cannot send calendar update: missing user or task")
        return False
    
    # Get property information for the task
    properties = task.properties
    
    property_names = ", ".join([p.name for p in properties])
    
    # Create notification content
    title = f"Calendar Update for Task: {task.title}"
    message = f"A calendar event related to your task '{task.title}' has been updated.\n"
    message += f"Due date: {task.due_date.strftime('%Y-%m-%d %H:%M') if task.due_date else 'No due date'}\n"
    message += f"Priority: {task.priority.value.capitalize()}\n"
    message += f"Property: {property_names}\n\n"
    message += f"Please check the task details for any changes."
    
    # Create in-app notification
    create_notification(
        user_id=user.id,
        task_id=task.id,
        notification_type=NotificationType.CALENDAR_UPDATE,
        channel=NotificationChannel.IN_APP,
        title=title,
        message=message
    )
    
    # Send email notification if enabled
    if current_app.config.get('NOTIFICATION_EMAIL_ENABLED', True):
        send_email_notification(
            user=user,
            subject=title,
            text_body=message,
            html_body=render_template('email/calendar_update.html', 
                                     user=user, 
                                     task=task,
                                     properties=properties)
        )
    
    # Send SMS notification if enabled and user has a phone number
    if current_app.config.get('NOTIFICATION_SMS_ENABLED', True) and hasattr(user, 'phone') and user.phone:
        thread = get_or_create_sms_thread(user.phone)
        
        sms_message = f"Calendar update for task: {task.title}. Please check the app for details."
        
        send_sms_notification(
            phone_number=user.phone,
            message=sms_message,
            thread_id=thread.id if thread else None
        )
    
    return True

def send_repair_request_notification(repair_request, property_owner):
    """Send notification when a repair request is submitted"""
    if not property_owner or not repair_request:
        current_app.logger.error("Cannot send repair request notification: missing property owner or repair request")
        return False
    
    # Create notification content
    title = f"New Repair Request: {repair_request.title}"
    message = f"A new repair request has been submitted for {repair_request.associated_property.name}:\n"
    message += f"Title: {repair_request.title}\n"
    message += f"Location: {repair_request.location}\n"
    message += f"Severity: {repair_request.severity.value.capitalize()}\n"
    message += f"Reported by: {repair_request.reporter.get_full_name()}\n\n"
    message += f"Description: {repair_request.description}"
    
    # Create in-app notification
    create_notification(
        user_id=property_owner.id,
        task_id=None,
        notification_type=NotificationType.REPAIR_REQUEST,
        channel=NotificationChannel.IN_APP,
        title=title,
        message=message
    )
    
    # Send email notification if enabled
    if current_app.config.get('NOTIFICATION_EMAIL_ENABLED', True):
        send_email_notification(
            user=property_owner,
            subject=title,
            text_body=message,
            html_body=f"<p>A new repair request has been submitted for <strong>{repair_request.associated_property.name}</strong>:</p>"
                     f"<p><strong>Title:</strong> {repair_request.title}<br>"
                     f"<strong>Location:</strong> {repair_request.location}<br>"
                     f"<strong>Severity:</strong> {repair_request.severity.value.capitalize()}<br>"
                     f"<strong>Reported by:</strong> {repair_request.reporter.get_full_name()}</p>"
                     f"<p><strong>Description:</strong><br>{repair_request.description}</p>"
                     f"<p>Please log in to review and take action on this request.</p>"
        )
    
    # Send SMS notification if enabled and user has a phone number
    if current_app.config.get('NOTIFICATION_SMS_ENABLED', True) and hasattr(property_owner, 'phone') and property_owner.phone:
        thread = get_or_create_sms_thread(property_owner.phone)
        
        sms_message = f"New repair request for {repair_request.associated_property.name}: {repair_request.title} ({repair_request.severity.value.capitalize()}). Please check the app for details."
        
        send_sms_notification(
            phone_number=property_owner.phone,
            message=sms_message,
            thread_id=thread.id if thread else None
        )
    
    return True

def send_inventory_low_notification(item, property, user):
    """Send notification when an inventory item falls below its reorder threshold"""
    if not user or not item or not property:
        current_app.logger.error("Cannot send inventory notification: missing user, item, or property")
        return False
    
    # Create notification content
    title = f"Low Inventory Alert: {item.name}"
    message = f"The inventory level for {item.name} at {property.name} is low.\n"
    message += f"Current quantity: {item.current_quantity} {item.unit_of_measure}\n"
    message += f"Reorder threshold: {item.reorder_threshold} {item.unit_of_measure}\n"
    message += f"Please restock this item soon."
    
    # Create in-app notification
    create_notification(
        user_id=user.id,
        task_id=None,
        notification_type=NotificationType.INVENTORY_LOW,
        channel=NotificationChannel.IN_APP,
        title=title,
        message=message
    )
    
    # Send email notification if enabled
    if current_app.config.get('NOTIFICATION_EMAIL_ENABLED', True):
        send_email_notification(
            user=user,
            subject=title,
            text_body=message,
            html_body=f"<p>The inventory level for <strong>{item.name}</strong> at <strong>{property.name}</strong> is low.</p>"
                     f"<p>Current quantity: {item.current_quantity} {item.unit_of_measure}<br>"
                     f"Reorder threshold: {item.reorder_threshold} {item.unit_of_measure}</p>"
                     f"<p>Please restock this item soon.</p>"
        )
    
    # Send SMS notification if enabled and user has a phone number
    if current_app.config.get('NOTIFICATION_SMS_ENABLED', True) and hasattr(user, 'phone') and user.phone:
        thread = get_or_create_sms_thread(user.phone)
        
        sms_message = f"Low inventory alert: {item.name} at {property.name} is below threshold ({item.current_quantity}/{item.reorder_threshold} {item.unit_of_measure})."
        
        send_sms_notification(
            phone_number=user.phone,
            message=sms_message,
            thread_id=thread.id if thread else None
        )
    
    return True

def send_direct_message_notification(sender, recipient, message_content, thread_id=None):
    """Send notification for direct messages between users"""
    if not sender or not recipient or not message_content:
        current_app.logger.error("Cannot send direct message notification: missing sender, recipient, or message")
        return False
    
    # Create notification content
    title = f"New Message from {sender.get_full_name()}"
    message = f"You have received a new message from {sender.get_full_name()}:\n\n{message_content}"
    
    # Create in-app notification
    create_notification(
        user_id=recipient.id,
        task_id=None,
        notification_type=NotificationType.INVITATION,  # Reuse invitation type for messages
        channel=NotificationChannel.IN_APP,
        title=title,
        message=message
    )
    
    # Send SMS notification if enabled and user has a phone number
    if (getattr(recipient, 'sms_notifications', False) and 
        current_app.config.get('NOTIFICATION_SMS_ENABLED', True) and 
        hasattr(recipient, 'phone') and recipient.phone):
        
        sms_message = f"New message from {sender.get_full_name()}: {message_content[:100]}{'...' if len(message_content) > 100 else ''}"
        
        send_sms_notification(
            phone_number=recipient.phone,
            message=sms_message,
            thread_id=thread_id
        )
    
    return True

def send_task_completion_notification(task, user, completed_by):
    """Send notification when a task is completed"""
    if not user or not task or not completed_by:
        current_app.logger.error("Cannot send task completion notification: missing user, task, or completed_by")
        return False
    
    # Create notification content
    title = f"Task Completed: {task.title}"
    message = f"Task '{task.title}' has been completed by {completed_by.get_full_name()}.\n"
    message += f"Completed at: {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}\n"
    if task.description:
        message += f"Description: {task.description}"
    
    # Create in-app notification
    create_notification(
        user_id=user.id,
        task_id=task.id,
        notification_type=NotificationType.TASK_COMPLETED,
        channel=NotificationChannel.IN_APP,
        title=title,
        message=message
    )
    
    # Send SMS notification if enabled and user has a phone number
    if (getattr(user, 'sms_notifications', False) and 
        current_app.config.get('NOTIFICATION_SMS_ENABLED', True) and 
        hasattr(user, 'phone') and user.phone):
        
        thread = get_or_create_sms_thread(user.phone)
        
        sms_message = f"Task '{task.title}' has been completed by {completed_by.get_full_name()}."
        
        send_sms_notification(
            phone_number=user.phone,
            message=sms_message,
            thread_id=thread.id if thread else None
        )
    
    return True

def create_notification(user_id, notification_type, channel, title, message, task_id=None):
    """Create a notification record in the database"""
    try:
        notification = Notification(
            recipient_id=user_id,
            notification_type=notification_type,
            message=message
        )
        
        db.session.add(notification)
        db.session.commit()
        
        current_app.logger.info(f"Created {channel.value} notification for user {user_id}")
        return notification
        
    except Exception as e:
        current_app.logger.error(f"Error creating notification: {str(e)}")
        db.session.rollback()
        return None

def send_email_notification(user, subject, text_body, html_body):
    """Send an email notification"""
    try:
        from app.common.email import send_email
        send_email(
            subject=subject,
            recipients=[user.email],
            text_body=text_body,
            html_body=html_body
        )
        current_app.logger.info(f"Email notification sent to {user.email}")
        return True
    except Exception as e:
        current_app.logger.error(f"Failed to send email notification: {str(e)}")
        return False

def send_sms_notification(phone_number, message, thread_id=None):
    """Send an SMS notification using Twilio with thread support"""
    try:
        from app.utils.sms import send_sms
        success, error = send_sms(phone_number, message, thread_id=thread_id)
        
        if success:
            current_app.logger.info(f"SMS notification sent successfully to {phone_number}")
            return True
        else:
            current_app.logger.error(f"Failed to send SMS notification to {phone_number}: {error}")
            return False
            
    except Exception as e:
        current_app.logger.error(f"Failed to send SMS notification: {str(e)}")
        return False

def get_or_create_sms_thread(phone_number):
    """Get or create an SMS thread for a phone number"""
    try:
        system_phone = current_app.config.get('TWILIO_PHONE_NUMBER')
        if not system_phone:
            return None
        
        # Format phone number
        formatted_phone = format_phone_number(phone_number)
        
        # Look for existing thread
        thread = MessageThread.query.filter_by(
            participant_phone=formatted_phone,
            system_phone=system_phone
        ).first()
        
        if not thread:
            # Create new thread
            thread = MessageThread(
                participant_phone=formatted_phone,
                system_phone=system_phone,
                status='active'
            )
            db.session.add(thread)
            db.session.commit()
            current_app.logger.info(f"Created new SMS thread for {formatted_phone}")
        
        return thread
        
    except Exception as e:
        current_app.logger.error(f"Error getting/creating SMS thread: {str(e)}")
        return None

def send_bulk_sms_notification(users, message, notification_type=NotificationType.TASK_ASSIGNMENT):
    """Send SMS notification to multiple users"""
    results = []
    
    for user in users:
        if hasattr(user, 'phone') and user.phone and getattr(user, 'sms_notifications', False):
            thread = get_or_create_sms_thread(user.phone)
            
            success = send_sms_notification(
                phone_number=user.phone,
                message=message,
                thread_id=thread.id if thread else None
            )
            
            results.append({
                'user_id': user.id,
                'phone': user.phone,
                'success': success
            })
        else:
            results.append({
                'user_id': user.id,
                'phone': getattr(user, 'phone', None),
                'success': False,
                'reason': 'No phone number or SMS notifications disabled'
            })
    
    return results