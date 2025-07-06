from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
from app.models import (
    Notification, NotificationChannel, NotificationType, 
    MessageThread, Message, User, Task, TaskAssignment, 
    TaskStatus, RepairRequest, RepairRequestSeverity
)
from app import db
import logging
from flask import current_app, has_app_context, request
import re
from datetime import datetime
import phonenumbers

LANGUAGE_TEMPLATES = {
    'task_assignment': {
        'en': 'New task assigned: {task_title}. Due: {due_date}.',
        'es': 'Nueva tarea asignada: {task_title}. Fecha límite: {due_date}.',
        'zh': '新任务分配: {task_title}。截止日期: {due_date}。',
    },
    'calendar_event': {
        'en': 'New event: {event_title} on {event_date}.',
        'es': 'Nuevo evento: {event_title} el {event_date}.',
        'zh': '新日程: {event_title}，时间: {event_date}。',
    },
}

def send_multilingual_sms(user, message_key, context):
    """
    Send an SMS to the user in their preferred language using a message template.
    message_key: 'task_assignment' or 'calendar_event'
    context: dict with template variables
    """
    if not user or not getattr(user, 'phone', None):
        return False, 'No phone number'
    language = getattr(user, 'language', 'en') or 'en'
    template = LANGUAGE_TEMPLATES.get(message_key, {}).get(language, LANGUAGE_TEMPLATES[message_key]['en'])
    message = template.format(**context)
    return send_sms(user.phone, message)

def send_sms(to_number, message, create_notification=False, thread_id=None):
    """Send an SMS message using Twilio with enhanced error handling"""
    if not has_app_context():
        logging.warning("No Flask application context available - SMS disabled")
        return False, "SMS disabled: No Flask application context"
    
    logger = getattr(current_app, 'logger', None) if current_app else None
    if logger is None:
        logger = logging.getLogger(__name__)
    
    # Format phone number
    formatted_number = format_phone_number(to_number)
    if not formatted_number:
        logger.error(f"Invalid phone number format: {to_number}")
        return False, f"Invalid phone number format: {to_number}"
    
    try:
        # Check if SMS is enabled
        if not current_app.config.get('NOTIFICATION_SMS_ENABLED', True):
            logger.warning("SMS notifications are disabled")
            return False, "SMS notifications are disabled"
            
        # Check if Twilio credentials are configured
        twilio_account_sid = current_app.config.get('TWILIO_ACCOUNT_SID')
        twilio_auth_token = current_app.config.get('TWILIO_AUTH_TOKEN')
        twilio_phone_number = current_app.config.get('TWILIO_PHONE_NUMBER')
        
        if not all([twilio_account_sid, twilio_auth_token, twilio_phone_number]):
            logger.warning("Twilio credentials are not configured - SMS will be disabled")
            missing_creds = []
            if not twilio_account_sid:
                missing_creds.append("TWILIO_ACCOUNT_SID")
            if not twilio_auth_token:
                missing_creds.append("TWILIO_AUTH_TOKEN")
            if not twilio_phone_number:
                missing_creds.append("TWILIO_PHONE_NUMBER")
            return False, f"SMS disabled: Missing Twilio credentials ({', '.join(missing_creds)})"
        
        # Initialize Twilio client with error handling
        try:
            client = Client(twilio_account_sid, twilio_auth_token)
            logger.info(f"Twilio client initialized successfully")
        except Exception as client_error:
            logger.error(f"Failed to initialize Twilio client: {str(client_error)}")
            return False, f"Twilio client initialization failed: {str(client_error)}"
        
        # Log the attempt with more details
        logger.info(f"Attempting to send SMS to {formatted_number} from {twilio_phone_number}")
        logger.debug(f"Message content: {message}")
        
        # Send the message with enhanced parameters
        try:
            # Get base URL for status callback, with fallback
            base_url = current_app.config.get('BASE_URL')
            if not base_url:
                logger.warning("BASE_URL not configured, using localhost fallback")
                base_url = 'http://localhost:5001'
            
            # Only include status callback if we have a valid base URL
            message_params = {
                'body': message,
                'from_': twilio_phone_number,
                'to': formatted_number
            }
            
            # Only add status callback if BASE_URL is properly configured
            if base_url and base_url != 'http://localhost:5001':
                message_params['status_callback'] = f"{base_url}/messages/status-callback"
            
            message_obj = client.messages.create(**message_params)
            
            # Log the Twilio response
            logger.info(f"Twilio response: {message_obj.sid} - Status: {message_obj.status}")
            
            # Store message in database if thread_id provided
            if thread_id:
                store_outgoing_message(thread_id, to_number, message, message_obj.sid)
            
            if create_notification:
                # Log the notification
                notification = Notification(
                    user_id=None,  # Will be set when user registers
                    notification_type=NotificationType.TASK_ASSIGNMENT,
                    channel=NotificationChannel.SMS,
                    title='Service Staff Invitation',
                    message=message,
                    status='sent',
                    external_id=message_obj.sid
                )
                db.session.add(notification)
                db.session.commit()
            
            logger.info(f"SMS sent successfully to {formatted_number}")
            return True, None
            
        except Exception as twilio_error:
            error_msg = str(twilio_error)
            logger.error(f"Twilio API error: {error_msg}")
            
            # Provide specific guidance for common Twilio errors
            if "not a Twilio phone number" in error_msg:
                logger.error(f"Twilio phone number {twilio_phone_number} is not valid for this account")
                logger.error("Please check your Twilio console and ensure:")
                logger.error("1. The phone number exists in your Twilio account")
                logger.error("2. The phone number is verified and approved for SMS")
                logger.error("3. The phone number matches the country of your recipients")
                error_msg = f"SMS failed: Invalid Twilio phone number {twilio_phone_number}. Please check your Twilio account configuration."
            elif "country mismatch" in error_msg:
                logger.error("Country mismatch between sender and recipient phone numbers")
                error_msg = "SMS failed: Country mismatch between sender and recipient phone numbers."
            
            # Store failed message in database if thread_id provided
            if thread_id:
                store_outgoing_message(thread_id, to_number, message, None, status='failed', error=error_msg)
            
            if create_notification:
                # Log the notification with error
                notification = Notification(
                    user_id=None,
                    notification_type=NotificationType.TASK_ASSIGNMENT,
                    channel=NotificationChannel.SMS,
                    title='Service Staff Invitation',
                    message=message,
                    status='failed',
                    error_message=error_msg
                )
                db.session.add(notification)
                db.session.commit()
            return False, error_msg
        
    except Exception as e:
        # Log the error
        logger.error(f"Failed to send SMS to {formatted_number}: {str(e)}")
        
        # Store failed message in database if thread_id provided
        if thread_id:
            store_outgoing_message(thread_id, to_number, message, None, status='failed', error=str(e))
        
        if create_notification:
            notification = Notification(
                user_id=None,  # Will be set when user registers
                notification_type=NotificationType.TASK_ASSIGNMENT,
                channel=NotificationChannel.SMS,
                title='Service Staff Invitation',
                message=message,
                status='failed',
                error_message=str(e)
            )
            db.session.add(notification)
            db.session.commit()
        
        return False, str(e)

def is_valid_phone_number(phone_number):
    """Validate phone number format (E.164)"""
    # Basic E.164 validation: +[country code][number]
    pattern = r'^\+[1-9]\d{1,14}$'
    return bool(re.match(pattern, phone_number))

def format_phone_number(phone, default_country='US'):
    """Format a phone number to E.164 for Twilio. Default to US if no country code."""
    if not phone:
        return None
    try:
        parsed = phonenumbers.parse(phone, default_country)
        if not phonenumbers.is_valid_number(parsed):
            return None
        return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
    except Exception:
        return None

def validate_twilio_config():
    """Validate Twilio configuration and provide helpful error messages"""
    if not has_app_context():
        return False, "No Flask application context"
    
    logger = getattr(current_app, 'logger', None) if current_app else None
    if logger is None:
        logger = logging.getLogger(__name__)
    
    # Check if SMS is enabled
    if not current_app.config.get('NOTIFICATION_SMS_ENABLED', True):
        return False, "SMS notifications are disabled"
    
    # Check Twilio credentials
    twilio_account_sid = current_app.config.get('TWILIO_ACCOUNT_SID')
    twilio_auth_token = current_app.config.get('TWILIO_AUTH_TOKEN')
    twilio_phone_number = current_app.config.get('TWILIO_PHONE_NUMBER')
    
    if not all([twilio_account_sid, twilio_auth_token, twilio_phone_number]):
        missing = []
        if not twilio_account_sid:
            missing.append("TWILIO_ACCOUNT_SID")
        if not twilio_auth_token:
            missing.append("TWILIO_AUTH_TOKEN")
        if not twilio_phone_number:
            missing.append("TWILIO_PHONE_NUMBER")
        return False, f"Missing Twilio configuration: {', '.join(missing)}"
    
    # Validate phone number format
    formatted_number = format_phone_number(twilio_phone_number)
    if not formatted_number:
        return False, f"Invalid Twilio phone number format: {twilio_phone_number}"
    
    # Try to initialize Twilio client
    try:
        client = Client(twilio_account_sid, twilio_auth_token)
        # Try to fetch the phone number to validate it exists in the account
        try:
            incoming_phone_numbers = client.incoming_phone_numbers.list(phone_number=formatted_number)
            if not incoming_phone_numbers:
                return False, f"Phone number {formatted_number} not found in Twilio account. Please verify it exists and is approved for SMS."
        except Exception as e:
            logger.warning(f"Could not validate Twilio phone number: {e}")
            # Continue anyway, as this might be a permissions issue
        
        return True, "Twilio configuration is valid"
        
    except Exception as e:
        return False, f"Failed to initialize Twilio client: {str(e)}"

def handle_incoming_sms():
    """Handle incoming SMS webhook from Twilio"""
    try:
        # Get webhook data from Twilio
        from_number = request.form.get('From')
        to_number = request.form.get('To')
        message_body = request.form.get('Body', '').strip()
        message_sid = request.form.get('MessageSid')
        
        logger = current_app.logger
        logger.info(f"Received SMS from {from_number} to {to_number}: {message_body}")
        
        # Find or create message thread
        thread = find_or_create_thread(from_number, to_number)
        
        # Store incoming message
        store_incoming_message(thread.id, from_number, message_body, message_sid)
        
        # Process message based on content
        response_message = process_incoming_message(thread, message_body, from_number)
        
        # Create TwiML response
        twiml = MessagingResponse()
        if response_message:
            twiml.message(response_message)
        
        return str(twiml)
        
    except Exception as e:
        current_app.logger.error(f"Error handling incoming SMS: {str(e)}")
        # Return empty TwiML response to avoid Twilio errors
        return str(MessagingResponse())

def find_or_create_thread(from_number, to_number):
    """Find existing thread or create new one for phone number pair"""
    try:
        # Look for existing thread
        thread = MessageThread.query.filter_by(
            participant_phone=from_number,
            system_phone=to_number
        ).first()
        
        if not thread:
            # Create new thread
            thread = MessageThread(
                participant_phone=from_number,
                system_phone=to_number,
                status='active'
            )
            db.session.add(thread)
            db.session.commit()
            current_app.logger.info(f"Created new message thread for {from_number}")
        
        return thread
        
    except Exception as e:
        current_app.logger.error(f"Error finding/creating thread: {str(e)}")
        db.session.rollback()
        raise

def store_incoming_message(thread_id, from_number, message_body, message_sid):
    """Store incoming message in database"""
    try:
        message = Message(
            thread_id=thread_id,
            direction='incoming',
            phone_number=from_number,
            content=message_body,
            external_id=message_sid,
            status='received'
        )
        db.session.add(message)
        db.session.commit()
        current_app.logger.info(f"Stored incoming message: {message_sid}")
        
    except Exception as e:
        current_app.logger.error(f"Error storing incoming message: {str(e)}")
        db.session.rollback()

def store_outgoing_message(thread_id, to_number, message_body, message_sid, status='sent', error=None):
    """Store outgoing message in database"""
    try:
        message = Message(
            thread_id=thread_id,
            direction='outgoing',
            phone_number=to_number,
            content=message_body,
            external_id=message_sid,
            status=status,
            error_message=error
        )
        db.session.add(message)
        db.session.commit()
        current_app.logger.info(f"Stored outgoing message: {message_sid}")
        
    except Exception as e:
        current_app.logger.error(f"Error storing outgoing message: {str(e)}")
        db.session.rollback()

def process_incoming_message(thread, message_body, from_number):
    """Process incoming message and return response"""
    try:
        # Convert message to lowercase for easier processing
        message_lower = message_body.lower().strip()
        
        # Check for help command
        if message_lower in ['help', 'h', '?']:
            return get_help_message()
        
        # Check for status command
        if message_lower in ['status', 's']:
            return get_status_message(thread)
        
        # Check for task commands
        if message_lower.startswith('task'):
            return process_task_command(thread, message_body)
        
        # Check for repair commands
        if message_lower.startswith('repair'):
            return process_repair_command(thread, message_body)
        
        # Default response for unrecognized messages
        return "Thanks for your message! Reply 'HELP' for available commands or contact support for assistance."
        
    except Exception as e:
        current_app.logger.error(f"Error processing incoming message: {str(e)}")
        return "Sorry, I encountered an error processing your message. Please try again or contact support."

def get_help_message():
    """Return help message with available commands"""
    return """Available commands:
• HELP - Show this help message
• STATUS - Check your current tasks and assignments
• TASK [id] - Get details about a specific task
• REPAIR [description] - Report a repair issue
• Contact support for other assistance"""

def get_status_message(thread):
    """Get status of user's tasks and assignments"""
    try:
        # Find user by phone number
        user = User.query.filter_by(phone=thread.participant_phone).first()
        
        if not user:
            return "Phone number not registered. Please contact support to link your phone number to your account."
        
        # Get user's active tasks
        active_tasks = Task.query.join(TaskAssignment).filter(
            TaskAssignment.user_id == user.id,
            Task.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS])
        ).limit(5).all()
        
        if not active_tasks:
            return "You have no active tasks at the moment."
        
        response = "Your active tasks:\n"
        for task in active_tasks:
            response += f"• Task {task.id}: {task.title} (Due: {task.due_date.strftime('%Y-%m-%d') if task.due_date else 'No due date'})\n"
        
        response += "\nReply 'TASK [id]' for details about a specific task."
        return response
        
    except Exception as e:
        current_app.logger.error(f"Error getting status message: {str(e)}")
        return "Sorry, I couldn't retrieve your status. Please try again or contact support."

def process_task_command(thread, message_body):
    """Process task-related commands"""
    try:
        # Extract task ID from message
        parts = message_body.split()
        if len(parts) < 2:
            return "Please specify a task ID. Example: TASK 123"
        
        try:
            task_id = int(parts[1])
        except ValueError:
            return "Invalid task ID. Please provide a number."
        
        # Find the task
        task = Task.query.get(task_id)
        if not task:
            return f"Task {task_id} not found."
        
        # Check if user has access to this task
        user = User.query.filter_by(phone=thread.participant_phone).first()
        if not user:
            return "Phone number not registered. Please contact support."
        
        assignment = TaskAssignment.query.filter_by(
            task_id=task_id,
            user_id=user.id
        ).first()
        
        if not assignment:
            return f"You don't have access to task {task_id}."
        
        # Return task details
        response = f"Task {task_id}: {task.title}\n"
        response += f"Status: {task.status.value}\n"
        response += f"Priority: {task.priority.value}\n"
        if task.due_date:
            response += f"Due: {task.due_date.strftime('%Y-%m-%d %H:%M')}\n"
        if task.description:
            response += f"Description: {task.description}\n"
        
        return response
        
    except Exception as e:
        current_app.logger.error(f"Error processing task command: {str(e)}")
        return "Sorry, I couldn't process your task request. Please try again."

def process_repair_command(thread, message_body):
    """Process repair request commands"""
    try:
        # Extract repair description
        parts = message_body.split(' ', 1)
        if len(parts) < 2:
            return "Please provide a description of the repair needed. Example: REPAIR Kitchen sink is leaking"
        
        description = parts[1]
        
        # Find user by phone number
        user = User.query.filter_by(phone=thread.participant_phone).first()
        if not user:
            return "Phone number not registered. Please contact support to link your phone number to your account."
        
        # Find user's properties
        properties = user.visible_properties
        if not properties:
            return "You don't have access to any properties. Please contact support."
        
        # For now, use the first property (could be enhanced to ask which property)
        property = properties[0]
        
        # Create repair request
        repair_request = RepairRequest(
            title=f"SMS Repair Request: {description[:50]}...",
            description=description,
            property_id=property.id,
            reporter_id=user.id,
            severity=RepairRequestSeverity.MEDIUM
        )
        
        db.session.add(repair_request)
        db.session.commit()
        
        return f"Repair request submitted for {property.name}. Request ID: {repair_request.id}. We'll contact you soon."
        
    except Exception as e:
        current_app.logger.error(f"Error processing repair command: {str(e)}")
        return "Sorry, I couldn't submit your repair request. Please try again or contact support."

def handle_status_callback():
    """Handle SMS status callback from Twilio"""
    try:
        message_sid = request.form.get('MessageSid')
        message_status = request.form.get('MessageStatus')
        
        current_app.logger.info(f"SMS status callback: {message_sid} - {message_status}")
        
        # Update message status in database
        message = Message.query.filter_by(external_id=message_sid).first()
        if message:
            message.status = message_status
            message.updated_at = datetime.utcnow()
            db.session.commit()
            current_app.logger.info(f"Updated message status: {message_sid} -> {message_status}")
        
        return '', 200
        
    except Exception as e:
        current_app.logger.error(f"Error handling status callback: {str(e)}")
        return '', 500 