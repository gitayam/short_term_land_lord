from twilio.rest import Client
from app.models import Notification, NotificationChannel, NotificationType
from app import db
import logging

def send_sms(to_number, message, create_notification=False):
    """Send an SMS message using Twilio"""
    from flask import current_app
    
    # Set up a fallback logger in case current_app.logger is not available
    logger = getattr(current_app, 'logger', None) if current_app else None
    if logger is None:
        logger = logging.getLogger(__name__)
    
    try:
        # Check if we have a Flask app context
        if not current_app:
            logger.warning("No Flask application context available - SMS disabled")
            return False, "SMS disabled: No Flask application context"
            
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
        logger.info(f"Attempting to send SMS to {to_number} from {twilio_phone_number}")
        logger.debug(f"Message content: {message}")
        
        # Send the message
        try:
            twilio_message = client.messages.create(
                body=message,
                from_=twilio_phone_number,
                to=to_number
            )
            
            # Log the Twilio response
            logger.info(f"Twilio response: {twilio_message.sid} - Status: {twilio_message.status}")
            
            if create_notification:
                # Log the notification
                notification = Notification(
                    user_id=None,  # Will be set when user registers
                    notification_type=NotificationType.TASK_ASSIGNMENT,
                    channel=NotificationChannel.SMS,
                    title='Service Staff Invitation',
                    message=message,
                    status='sent',
                    external_id=twilio_message.sid
                )
                db.session.add(notification)
                db.session.commit()
            
            logger.info(f"SMS sent successfully to {to_number}")
            return True, None
            
        except Exception as twilio_error:
            logger.error(f"Twilio API error: {str(twilio_error)}")
            if create_notification:
                # Log the notification with error
                notification = Notification(
                    user_id=None,
                    notification_type=NotificationType.TASK_ASSIGNMENT,
                    channel=NotificationChannel.SMS,
                    title='Service Staff Invitation',
                    message=message,
                    status='failed',
                    error_message=str(twilio_error)
                )
                db.session.add(notification)
                db.session.commit()
            return False, str(twilio_error)
        
    except Exception as e:
        # Log the error
        logger.error(f"Failed to send SMS to {to_number}: {str(e)}")
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