from twilio.rest import Client
from flask import current_app
from app.models import Notification, NotificationChannel, NotificationType
from app import db

def send_sms(to_number, message, create_notification=False):
    """Send an SMS message using Twilio"""
    try:
        # Check if SMS is enabled
        if not current_app.config.get('NOTIFICATION_SMS_ENABLED', True):
            current_app.logger.warning("SMS notifications are disabled")
            return False, "SMS notifications are disabled"
            
        # Check if Twilio credentials are configured
        if not all([
            current_app.config.get('TWILIO_ACCOUNT_SID'),
            current_app.config.get('TWILIO_AUTH_TOKEN'),
            current_app.config.get('TWILIO_PHONE_NUMBER')
        ]):
            current_app.logger.error("Twilio credentials are not properly configured")
            return False, "Twilio credentials are not properly configured"
            
        # Initialize Twilio client
        client = Client(
            current_app.config['TWILIO_ACCOUNT_SID'],
            current_app.config['TWILIO_AUTH_TOKEN']
        )
        
        # Log the attempt with more details
        current_app.logger.info(f"Attempting to send SMS to {to_number} from {current_app.config['TWILIO_PHONE_NUMBER']}")
        current_app.logger.debug(f"Message content: {message}")
        
        # Send the message
        try:
            twilio_message = client.messages.create(
                body=message,
                from_=current_app.config['TWILIO_PHONE_NUMBER'],
                to=to_number
            )
            
            # Log the Twilio response
            current_app.logger.info(f"Twilio response: {twilio_message.sid} - Status: {twilio_message.status}")
            
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
            
            current_app.logger.info(f"SMS sent successfully to {to_number}")
            return True, None
            
        except Exception as twilio_error:
            current_app.logger.error(f"Twilio API error: {str(twilio_error)}")
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
        current_app.logger.error(f"Failed to send SMS to {to_number}: {str(e)}")
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