#!/usr/bin/env python3
"""
Database persistence utilities for App Engine deployment
Handles SQLite backup/restore to/from Cloud Storage for better persistence
"""

import os
import logging
import shutil
from datetime import datetime
from google.cloud import storage
from flask import current_app

logger = logging.getLogger(__name__)

class DatabasePersistence:
    """Handles database backup and restore operations"""
    
    def __init__(self, app=None):
        self.app = app
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize with Flask app"""
        self.bucket_name = app.config.get('BACKUP_BUCKET', 'speech-memorization-backups')
        self.backup_enabled = app.config.get('DATABASE_BACKUP_ENABLED', 'false').lower() == 'true'
        self.db_path = self._extract_db_path(app.config.get('DATABASE_URL', ''))
        
        if self.backup_enabled:
            logger.info(f"Database persistence enabled for bucket: {self.bucket_name}")
    
    def _extract_db_path(self, database_url):
        """Extract file path from SQLite database URL"""
        if database_url.startswith('sqlite:///'):
            return database_url[10:]  # Remove 'sqlite:///'
        return database_url
    
    def ensure_data_directory(self):
        """Ensure the data directory exists"""
        if self.db_path:
            db_dir = os.path.dirname(self.db_path)
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir, exist_ok=True)
                logger.info(f"Created database directory: {db_dir}")
    
    def restore_from_backup(self):
        """Restore database from Cloud Storage if available"""
        if not self.backup_enabled or not self.db_path:
            return False
        
        try:
            # Ensure directory exists
            self.ensure_data_directory()
            
            # Skip if database already exists
            if os.path.exists(self.db_path):
                logger.info(f"Database already exists at {self.db_path}")
                return False
            
            # Try to restore from Cloud Storage
            client = storage.Client()
            bucket = client.bucket(self.bucket_name)
            blob = bucket.blob('landlord.db')
            
            if blob.exists():
                blob.download_to_filename(self.db_path)
                logger.info(f"Restored database from Cloud Storage backup")
                return True
            else:
                logger.info("No backup found in Cloud Storage, starting fresh")
                return False
                
        except Exception as e:
            logger.error(f"Failed to restore database backup: {e}")
            return False
    
    def backup_to_cloud(self):
        """Backup database to Cloud Storage"""
        if not self.backup_enabled or not self.db_path or not os.path.exists(self.db_path):
            return False
        
        try:
            client = storage.Client()
            bucket = client.bucket(self.bucket_name)
            
            # Create timestamped backup
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            backup_blob = bucket.blob(f'backups/landlord_{timestamp}.db')
            backup_blob.upload_from_filename(self.db_path)
            
            # Update latest backup
            latest_blob = bucket.blob('landlord.db')
            latest_blob.upload_from_filename(self.db_path)
            
            logger.info(f"Database backed up to Cloud Storage")
            return True
            
        except Exception as e:
            logger.error(f"Failed to backup database: {e}")
            return False
    
    def periodic_backup(self):
        """Perform periodic backup (to be called from cron job)"""
        return self.backup_to_cloud()

def init_database_persistence(app):
    """Initialize database persistence for the app"""
    persistence = DatabasePersistence(app)
    
    # Try to restore from backup on startup
    if persistence.backup_enabled:
        persistence.restore_from_backup()
    
    return persistence