from app.models import MessageThread, Message, Notification, User
from flask_login import current_user
from sqlalchemy import or_
from datetime import datetime

def get_unified_messages(user):
    """
    Aggregate and normalize all message types (SMS, notifications, direct) for the current user.
    Returns a list of dicts sorted by timestamp descending.
    """
    # SMS Threads
    sms_threads = MessageThread.query.filter(
        or_(MessageThread.user_id == user.id, MessageThread.participant_phone == user.phone)
    ).all()
    sms_messages = []
    for thread in sms_threads:
        for msg in thread.messages:
            sms_messages.append({
                'type': 'sms',
                'id': msg.id,
                'thread_id': thread.id,
                'sender': msg.phone_number,
                'recipient': thread.participant_phone,
                'content': msg.content,
                'timestamp': msg.created_at,
                'read': msg.read,
            })

    # In-app Notifications
    notifications = Notification.query.filter_by(recipient_id=user.id).all()
    notification_messages = []
    for n in notifications:
        notification_messages.append({
            'type': 'notification',
            'id': n.id,
            'sender': 'System',
            'recipient': user.get_full_name() if hasattr(user, 'get_full_name') else user.email,
            'content': n.message,
            'timestamp': n.created_at,
            'read': n.read,
        })

    # TODO: Add direct messages if/when model exists
    # direct_messages = ...

    # Combine and sort all messages
    all_messages = sms_messages + notification_messages # + direct_messages
    all_messages.sort(key=lambda m: m['timestamp'] or datetime.min, reverse=True)
    return all_messages 