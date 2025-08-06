#!/usr/bin/env python3
"""
Database backup script for scheduled execution
Can be run as a cron job or Cloud Scheduler job
"""

from app import create_app
from app.utils.database_persistence import DatabasePersistence

def backup_database():
    """Backup database to Cloud Storage"""
    app = create_app()
    
    with app.app_context():
        persistence = DatabasePersistence(app)
        success = persistence.backup_to_cloud()
        
        if success:
            app.logger.info("✅ Database backup completed successfully")
            return True
        else:
            app.logger.error("❌ Database backup failed")
            return False

if __name__ == "__main__":
    backup_database()