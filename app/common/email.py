"""
Email utility functions for sending asynchronous emails using Flask-Mail.
"""
from threading import Thread
from flask import current_app
from flask_mail import Message
from app import mail

def send_async_email(app, msg):
    """Send an email message asynchronously within the given app context."""
    with app.app_context():
        mail.send(msg)

def send_email(subject, sender, recipients, text_body, html_body):
    """Compose and send an email asynchronously."""
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    # Using _get_current_object() is a common Flask pattern for passing app context to threads.
    Thread(target=send_async_email,
           args=(current_app._get_current_object(), msg)).start()