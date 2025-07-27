#!/usr/bin/env python
import os
import sys
import requests
import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler

# Add the parent directory to the path so we can import the app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app import create_app, db
from app.models import PropertyCalendar, Task
from app.tasks.notifications import notify_calendar_changes
try:
    from icalendar import Calendar
    ICALENDAR_AVAILABLE = True
except ImportError:
    Calendar = None
    ICALENDAR_AVAILABLE = False
from sqlalchemy.exc import SQLAlchemyError

# Configure logging
log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log_file = 'calendar_sync.log'
handler = RotatingFileHandler(log_file, maxBytes=10485760, backupCount=10)
handler.setFormatter(log_formatter)

logger = logging.getLogger('calendar_sync')
logger.setLevel(logging.INFO)
logger.addHandler(handler)
logger.addHandler(logging.StreamHandler())

def sync_calendars():
    """Sync all property calendars"""
    app = create_app()
    
    with app.app_context():
        logger.info("Starting calendar sync process")
        
        # Get all calendars
        try:
            calendars = PropertyCalendar.query.all()
            logger.info(f"Found {len(calendars)} calendars to sync")
        except Exception as e:
            logger.critical(f"Failed to retrieve calendars from database: {str(e)}", exc_info=True)
            return
        
        success_count = 0
        error_count = 0
        updated_calendars = []
        
        for calendar in calendars:
            try:
                logger.info(f"Syncing calendar {calendar.id} - {calendar.name}")
                
                # Fetch the iCal data
                try:
                    response = requests.get(calendar.ical_url, timeout=10)
                    if response.status_code == 200:
                        # Try to parse the iCal data to validate
                        if not ICALENDAR_AVAILABLE or Calendar is None:
                            raise ValueError("iCalendar library not available")
                        cal = Calendar.from_ical(response.text)
                        
                        # Set sync status
                        calendar.last_synced = datetime.utcnow()
                        calendar.sync_status = 'Success'
                        calendar.sync_error = None
                        
                        # Track updated calendars for notifications
                        updated_calendars.append(calendar.id)
                        
                        logger.info(f"Calendar {calendar.id} synced successfully")
                        success_count += 1
                    else:
                        # Update sync status
                        calendar.sync_status = 'Error'
                        calendar.sync_error = f"HTTP error: {response.status_code}"
                        logger.error(f"Calendar {calendar.id} sync error: HTTP {response.status_code}")
                        error_count += 1
                except requests.exceptions.Timeout:
                    # Specific handling for timeout errors
                    calendar.sync_status = 'Failed'
                    calendar.sync_error = "Request timed out after 10 seconds"
                    logger.error(f"Calendar {calendar.id} sync timed out")
                    error_count += 1
                except requests.exceptions.RequestException as e:
                    # Network-related error
                    calendar.sync_status = 'Failed'
                    calendar.sync_error = f"Request error: {str(e)}"[:255]
                    logger.error(f"Calendar {calendar.id} request error: {str(e)}")
                    error_count += 1
                except Exception as e:
                    # Other errors
                    calendar.sync_status = 'Failed'
                    calendar.sync_error = str(e)[:255]  # Limit error message length
                    logger.error(f"Calendar {calendar.id} sync failed: {str(e)}")
                    error_count += 1
            
                # Save the calendar status
                try:
                    db.session.commit()
                except SQLAlchemyError as e:
                    db.session.rollback()
                    logger.error(f"Database error while updating calendar {calendar.id}: {str(e)}")
            except Exception as e:
                logger.error(f"Unexpected error processing calendar {calendar.id}: {str(e)}", exc_info=True)
                error_count += 1
        
        # Send notifications for tasks affected by calendar changes
        if updated_calendars:
            try:
                # Get the property IDs associated with the updated calendars
                property_ids = [calendar.property_id for calendar in PropertyCalendar.query.filter(
                    PropertyCalendar.id.in_(updated_calendars)).all()]
                
                # Find tasks linked to the properties with updated calendars
                affected_tasks = Task.query.filter(Task.property_id.in_(property_ids)).all()
                affected_task_ids = [task.id for task in affected_tasks]
                
                if affected_task_ids:
                    logger.info(f"Sending notifications for {len(affected_task_ids)} affected tasks")
                    notify_calendar_changes(affected_task_ids)
            except Exception as e:
                logger.error(f"Error sending calendar update notifications: {str(e)}")
        
        logger.info(f"Calendar sync completed. Success: {success_count}, Errors: {error_count}")

if __name__ == "__main__":
    try:
        sync_calendars()
    except Exception as e:
        logger.critical(f"Critical error in calendar sync: {str(e)}", exc_info=True) 