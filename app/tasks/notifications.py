from flask import current_app
from app.models import Task, TaskAssignment, User, Notification, NotificationType
from app.notifications.service import (
    send_task_assignment_notification,
    send_task_reminder_notification,
    send_calendar_update_notification,
    check_upcoming_tasks
)
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

def schedule_task_reminders():
    """Schedule reminders for upcoming tasks"""
    try:
        check_upcoming_tasks()
        return True
    except Exception as e:
        logger.error(f"Error scheduling task reminders: {str(e)}")
        return False

def notify_calendar_changes(task_ids):
    """Send notifications for tasks affected by calendar changes"""
    if not task_ids:
        return False

    try:
        tasks = Task.query.filter(Task.id.in_(task_ids)).all()

        for task in tasks:
            # Notify all assigned users
            for assignment in task.assignments:
                if assignment.user_id:
                    user = User.query.get(assignment.user_id)
                    if user:
                        send_calendar_update_notification(task, user)

        return True
    except Exception as e:
        logger.error(f"Error sending calendar change notifications: {str(e)}")
        return False

def notify_task_assignment(task_id, user_id):
    """Send notification for a specific task assignment"""
    try:
        task = Task.query.get(task_id)
        user = User.query.get(user_id)

        if task and user:
            return send_task_assignment_notification(task, user)
        return False
    except Exception as e:
        logger.error(f"Error sending task assignment notification: {str(e)}")
        return False

def notify_task_due_soon(task_id):
    """Send reminders for a specific task that is due soon"""
    try:
        task = Task.query.get(task_id)

        if not task:
            return False

        # Notify all assigned users
        for assignment in task.assignments:
            if assignment.user_id:
                user = User.query.get(assignment.user_id)
                if user:
                    send_task_reminder_notification(task, user)

        return True
    except Exception as e:
        logger.error(f"Error sending task reminder notification: {str(e)}")
        return False
