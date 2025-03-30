from flask import current_app, render_template
from flask_mail import Message
from app import mail
from app.models import PasswordReset

def send_email(subject, recipients, text_body, html_body):
    msg = Message(
        subject=subject,
        recipients=recipients,
        body=text_body,
        html=html_body
    )
    mail.send(msg)

def send_password_reset_email(user):
    token = PasswordReset.create_token(user)
    send_email(
        subject='Reset Your Password',
        recipients=[user.email],
        text_body=render_template('email/reset_password.txt', user=user, token=token),
        html_body=render_template('email/reset_password.html', user=user, token=token)
    )
