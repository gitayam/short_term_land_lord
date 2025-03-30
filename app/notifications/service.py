from flask import current_app, render_template
from app import db
from app.models import Notification, NotificationType, NotificationChannel, User, Task, Property
from app.auth.email import send_email
from datetime import datetime, timedelta
import requests
from twilio.rest import Client
import logging

logger = logging.getLogger(__name__)

def send_task_assignment_notification(task, user):
    """Send notification when a task is assigned to a user"""
    if not user or not task:
        logger.error("Cannot send notification: missing user or task")
        return False
    
    # Get property information for the task
    properties = []
    for tp in task.properties:
        properties.append(tp.property)
    
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
    
    # Send email notification if enabled
    if current_app.config.get('NOTIFICATION_EMAIL_ENABLED', True):
        send_email_notification(
            user=user,
            subject=title,
            text_body=message,
            html_body=render_template('email/task_assignment.html', 
                                     user=user, 
                                     task=task,
                                     properties=properties)
        )
    
    # Send SMS notification if enabled and user has a phone number
    if current_app.config.get('NOTIFICATION_SMS_ENABLED', True) and hasattr(user, 'phone'):
        send_sms_notification(
            phone_number=user.phone,
            message=f"New task assigned: {task.title}. Due: {task.due_date.strftime('%Y-%m-%d') if task.due_date else 'No due date'}. Priority: {task.priority.value.capitalize()}."
        )
    
    return True

def send_task_reminder_notification(task, user):
    """Send reminder notification for upcoming tasks"""
    if not user or not task:
        logger.error("Cannot send reminder: missing user or task")
        return False
    
    # Get property information for the task
    properties = []
    for tp in task.properties:
        properties.append(tp.property)
    
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
    if current_app.config.get('NOTIFICATION_SMS_ENABLED', True) and hasattr(user, 'phone'):
        send_sms_notification(
            phone_number=user.phone,
            message=f"Reminder: Task '{task.title}' is due soon. Due: {task.due_date.strftime('%Y-%m-%d') if task.due_date else 'No due date'}."
        )
    
    return True

def send_calendar_update_notification(task, user):
    """Send notification when a calendar event affecting a task is updated"""
    if not user or not task:
        logger.error("Cannot send calendar update: missing user or task")
        return False
    
    # Get property information for the task
    properties = []
    for tp in task.properties:
        properties.append(tp.property)
    
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
    if current_app.config.get('NOTIFICATION_SMS_ENABLED', True) and hasattr(user, 'phone'):
        send_sms_notification(
            phone_number=user.phone,
            message=f"Calendar update for task: {task.title}. Please check the app for details."
        )
    
    return True

def send_repair_request_notification(repair_request, property_owner):
    """Send notification when a repair request is submitted"""
    if not property_owner or not repair_request:
        logger.error("Cannot send repair request notification: missing property owner or repair request")
        return False
    
    # Create notification content
    title = f"New Repair Request: {repair_request.title}"
    message = f"A new repair request has been submitted for {repair_request.property.name}:\n"
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
            html_body=f"<p>A new repair request has been submitted for <strong>{repair_request.property.name}</strong>:</p>"
                     f"<p><strong>Title:</strong> {repair_request.title}<br>"
                     f"<strong>Location:</strong> {repair_request.location}<br>"
                     f"<strong>Severity:</strong> {repair_request.severity.value.capitalize()}<br>"
                     f"<strong>Reported by:</strong> {repair_request.reporter.get_full_name()}</p>"
                     f"<p><strong>Description:</strong><br>{repair_request.description}</p>"
                     f"<p>Please log in to review and take action on this request.</p>"
        )
    
    # Send SMS notification if enabled and user has a phone number
    if current_app.config.get('NOTIFICATION_SMS_ENABLED', True) and hasattr(property_owner, 'phone'):
        send_sms_notification(
            phone_number=property_owner.phone,
            message=f"New repair request for {repair_request.property.name}: {repair_request.title} ({repair_request.severity.value.capitalize()}). Please check the app for details."
        )
    
    return True

def create_notification(user_id, notification_type, channel, title, message, task_id=None):
    """Create a notification record in the database"""
    notification = Notification(
        user_id=user_id,
        task_id=task_id,
        notification_type=notification_type,
        channel=channel,
        title=title,
        message=message
    )
    
    db.session.add(notification)
    db.session.commit()
    
    return notification

def send_email_notification(user, subject, text_body, html_body):
    """Send an email notification"""
    try:
        send_email(
            subject=subject,
            recipients=[user.email],
            text_body=text_body,
            html_body=html_body
        )
        return True
    except Exception as e:
        logger.error(f"Failed to send email notification: {str(e)}")
        return False

def send_sms_notification(phone_number, message):
    """Send an SMS notification using Twilio"""
    try:
        # Initialize Twilio client
        client = Client(
            current_app.config.get('TWILIO_ACCOUNT_SID'),
            current_app.config.get('TWILIO_AUTH_TOKEN')
        )
        
        # Send SMS
        client.messages.create(
            body=message,
            from_=current_app.config.get('TWILIO_PHONE_NUMBER'),
            to=phone_number
        )
        
        return True
    except Exception as e:
        logger.error(f"Failed to send SMS notification: {str(e)}")
        return False

def send_inventory_low_notification(item, property, user):
    """Send notification when an inventory item falls below its reorder threshold"""
    if not user or not item or not property:
        logger.error("Cannot send inventory notification: missing user, item, or property")
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
    if current_app.config.get('NOTIFICATION_SMS_ENABLED', True) and hasattr(user, 'phone'):
        send_sms_notification(
            phone_number=user.phone,
            message=f"Low inventory alert: {item.name} at {property.name} is below threshold ({item.current_quantity}/{item.reorder_threshold} {item.unit_of_measure})."
        )
    
    return True

def check_upcoming_tasks():
    """Check for tasks due soon and send reminders"""
    # Get reminder hours from config
    reminder_hours = current_app.config.get('NOTIFICATION_REMINDER_HOURS', 24)
    
    # Calculate the time threshold
    now = datetime.utcnow()
    reminder_threshold = now + timedelta(hours=reminder_hours)
    
    # Find tasks that are due within the reminder threshold
    upcoming_tasks = Task.query.filter(
        Task.due_date.isnot(None),
        Task.due_date <= reminder_threshold,
        Task.due_date > now,
        Task.status != 'completed'
    ).all()
    
    for task in upcoming_tasks:
        # Get all users assigned to this task
        for assignment in task.assignments:
            if assignment.user_id:
                # Check if a reminder has already been sent recently
                recent_reminder = Notification.query.filter_by(
                    user_id=assignment.user_id,
                    task_id=task.id,
                    notification_type=NotificationType.TASK_REMINDER
                ).filter(
                    Notification.sent_at > (now - timedelta(hours=reminder_hours))
                ).first()
                
                if not recent_reminder:
                    # Send reminder notification
                    send_task_reminder_notification(task, assignment.user)