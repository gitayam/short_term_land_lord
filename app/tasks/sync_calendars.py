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
from app.models import PropertyCalendar
from icalendar import Calendar
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
        calendars = PropertyCalendar.query.all()
        logger.info(f"Found {len(calendars)} calendars to sync")
        
        success_count = 0
        error_count = 0
        
        for calendar in calendars:
            try:
                logger.info(f"Syncing calendar {calendar.id} - {calendar.name}")
                
                # Fetch the iCal data
                response = requests.get(calendar.ical_url, timeout=10)
                if response.status_code == 200:
                    # Try to parse the iCal data to validate
                    cal = Calendar.from_ical(response.text)
                    
                    # Set sync status
                    calendar.last_synced = datetime.utcnow()
                    calendar.sync_status = 'Success'
                    calendar.sync_error = None
                    
                    logger.info(f"Calendar {calendar.id} synced successfully")
                    success_count += 1
                else:
                    # Update sync status
                    calendar.sync_status = 'Error'
                    calendar.sync_error = f"HTTP error: {response.status_code}"
                    logger.error(f"Calendar {calendar.id} sync error: HTTP {response.status_code}")
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
        
        logger.info(f"Calendar sync completed. Success: {success_count}, Errors: {error_count}")

if __name__ == "__main__":
    try:
        sync_calendars()
    except Exception as e:
        logger.critical(f"Critical error in calendar sync: {str(e)}", exc_info=True) 