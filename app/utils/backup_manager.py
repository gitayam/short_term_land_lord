"""
Automated Database Backup and Recovery System

This module provides comprehensive backup capabilities including automated
database backups, file backups, cloud storage integration, and recovery procedures.
"""

import subprocess
import os
import logging
import shutil
import gzip
import tarfile
from datetime import datetime, timedelta
from flask import current_app
from pathlib import Path
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
import psutil

logger = logging.getLogger(__name__)

class BackupManager:
    """Comprehensive backup management system"""
    
    def __init__(self):
        self.backup_dir = None
        self.s3_bucket = None
        self.retention_days = 7
        self.aws_access_key = None
        self.aws_secret_key = None
        self.aws_region = 'us-east-1'
        self._initialize_config()
    
    def _initialize_config(self):
        """Initialize backup configuration from Flask app config"""
        if current_app:
            self.backup_dir = current_app.config.get('BACKUP_DIR', '/app/backups')
            self.s3_bucket = current_app.config.get('AWS_S3_BUCKET')
            self.retention_days = int(current_app.config.get('BACKUP_RETENTION_DAYS', 7))
            self.aws_access_key = current_app.config.get('AWS_ACCESS_KEY_ID')
            self.aws_secret_key = current_app.config.get('AWS_SECRET_ACCESS_KEY')
            self.aws_region = current_app.config.get('AWS_S3_REGION', 'us-east-1')
    
    def create_database_backup(self):
        """Create complete database backup"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"db_backup_{timestamp}.sql.gz"
        backup_path = os.path.join(self.backup_dir, backup_filename)
        
        try:
            # Ensure backup directory exists
            os.makedirs(self.backup_dir, exist_ok=True)
            
            # Get database connection info
            db_uri = current_app.config.get('SQLALCHEMY_DATABASE_URI')
            if not db_uri:
                raise ValueError("Database URI not configured")
            
            # Parse database URI
            db_config = self._parse_db_uri(db_uri)
            
            if db_config['type'] == 'postgresql':
                success = self._backup_postgresql(db_config, backup_path)
            elif db_config['type'] == 'sqlite':
                success = self._backup_sqlite(db_config, backup_path)
            else:
                raise ValueError(f"Unsupported database type: {db_config['type']}")
            
            if success:
                # Verify backup file was created and has content
                if os.path.exists(backup_path) and os.path.getsize(backup_path) > 0:
                    logger.info(f"Database backup created successfully: {backup_filename}")
                    
                    # Upload to S3 if configured
                    if self.s3_bucket:
                        s3_success = self.upload_to_s3(backup_path, f"database/{backup_filename}")
                        if not s3_success:
                            logger.warning("S3 upload failed, but local backup succeeded")
                    
                    return backup_path
                else:
                    logger.error("Backup file was not created or is empty")
                    return None
            else:
                logger.error("Database backup failed")
                return None
                
        except Exception as e:
            logger.error(f"Database backup error: {str(e)}")
            return None
    
    def _parse_db_uri(self, db_uri):
        """Parse database URI to extract connection parameters"""
        if db_uri.startswith('postgresql://'):
            # postgresql://user:password@host:port/database
            parts = db_uri.replace('postgresql://', '').split('/')
            database = parts[-1]
            user_pass_host = parts[0]
            
            if '@' in user_pass_host:
                user_pass, host_port = user_pass_host.split('@')
                if ':' in user_pass:
                    user, password = user_pass.split(':', 1)
                else:
                    user = user_pass
                    password = ''
            else:
                host_port = user_pass_host
                user = 'postgres'
                password = ''
            
            if ':' in host_port:
                host, port = host_port.split(':')
            else:
                host = host_port
                port = '5432'
            
            return {
                'type': 'postgresql',
                'host': host,
                'port': port,
                'user': user,
                'password': password,
                'database': database
            }
        
        elif db_uri.startswith('sqlite:///'):
            db_path = db_uri.replace('sqlite:///', '')
            return {
                'type': 'sqlite',
                'path': db_path
            }
        
        else:
            raise ValueError(f"Unsupported database URI format: {db_uri}")
    
    def _backup_postgresql(self, db_config, backup_path):
        """Create PostgreSQL backup using pg_dump"""
        try:
            # Set environment variables for pg_dump
            env = os.environ.copy()
            if db_config['password']:
                env['PGPASSWORD'] = db_config['password']
            
            # Build pg_dump command
            cmd = [
                'pg_dump',
                '-h', db_config['host'],
                '-p', db_config['port'],
                '-U', db_config['user'],
                '-d', db_config['database'],
                '--no-password',
                '--verbose',
                '--clean',
                '--if-exists',
                '--create'
            ]
            
            # Execute pg_dump and compress output
            with open(backup_path, 'wb') as f:
                with gzip.GzipFile(fileobj=f, mode='wb') as gz:
                    process = subprocess.Popen(
                        cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        env=env
                    )
                    
                    # Stream output to compressed file
                    for line in process.stdout:
                        gz.write(line)
                    
                    process.wait()
            
            if process.returncode == 0:
                logger.info("PostgreSQL backup completed successfully")
                return True
            else:
                stderr_output = process.stderr.read().decode()
                logger.error(f"pg_dump failed: {stderr_output}")
                return False
                
        except Exception as e:
            logger.error(f"PostgreSQL backup error: {str(e)}")
            return False
    
    def _backup_sqlite(self, db_config, backup_path):
        """Create SQLite backup"""
        try:
            source_path = db_config['path']
            
            if not os.path.exists(source_path):
                logger.error(f"SQLite database file not found: {source_path}")
                return False
            
            # Copy and compress SQLite file
            with open(source_path, 'rb') as f_in:
                with gzip.open(backup_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            logger.info("SQLite backup completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"SQLite backup error: {str(e)}")
            return False
    
    def create_files_backup(self, include_paths=None):
        """Create backup of application files"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"files_backup_{timestamp}.tar.gz"
        backup_path = os.path.join(self.backup_dir, backup_filename)
        
        # Default paths to backup
        if include_paths is None:
            include_paths = [
                current_app.config.get('LOCAL_STORAGE_PATH', '/app/uploads'),
                '/app/logs'
            ]
        
        try:
            os.makedirs(self.backup_dir, exist_ok=True)
            
            with tarfile.open(backup_path, 'w:gz') as tar:
                for path in include_paths:
                    if os.path.exists(path):
                        # Add path to archive with relative path
                        arcname = os.path.relpath(path, '/')
                        tar.add(path, arcname=arcname)
                        logger.info(f"Added {path} to files backup")
                    else:
                        logger.warning(f"Path not found for backup: {path}")
            
            if os.path.exists(backup_path) and os.path.getsize(backup_path) > 0:
                logger.info(f"Files backup created successfully: {backup_filename}")
                
                # Upload to S3 if configured
                if self.s3_bucket:
                    self.upload_to_s3(backup_path, f"files/{backup_filename}")
                
                return backup_path
            else:
                logger.error("Files backup failed - no content")
                return None
                
        except Exception as e:
            logger.error(f"Files backup error: {str(e)}")
            return None
    
    def upload_to_s3(self, local_path, s3_key):
        """Upload backup file to S3"""
        if not self.s3_bucket:
            logger.warning("S3 bucket not configured")
            return False
        
        try:
            # Initialize S3 client
            s3_client = boto3.client(
                's3',
                aws_access_key_id=self.aws_access_key,
                aws_secret_access_key=self.aws_secret_key,
                region_name=self.aws_region
            )
            
            # Upload file
            s3_client.upload_file(
                local_path,
                self.s3_bucket,
                s3_key,
                ExtraArgs={
                    'ServerSideEncryption': 'AES256',
                    'StorageClass': 'STANDARD_IA'  # Cost-effective for backups
                }
            )
            
            logger.info(f"Successfully uploaded {local_path} to S3: s3://{self.s3_bucket}/{s3_key}")
            return True
            
        except NoCredentialsError:
            logger.error("AWS credentials not configured")
            return False
        except ClientError as e:
            logger.error(f"S3 upload failed: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"S3 upload error: {str(e)}")
            return False
    
    def cleanup_old_backups(self):
        """Remove old backup files based on retention policy"""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.retention_days)
            removed_count = 0
            
            # Clean local backups
            if os.path.exists(self.backup_dir):
                for filename in os.listdir(self.backup_dir):
                    if filename.startswith(('db_backup_', 'files_backup_')):
                        filepath = os.path.join(self.backup_dir, filename)
                        file_mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
                        
                        if file_mtime < cutoff_date:
                            os.remove(filepath)
                            removed_count += 1
                            logger.info(f"Removed old backup: {filename}")
            
            # Clean S3 backups if configured
            if self.s3_bucket and self.aws_access_key:
                removed_count += self._cleanup_s3_backups(cutoff_date)
            
            logger.info(f"Cleanup completed: removed {removed_count} old backups")
            return removed_count
            
        except Exception as e:
            logger.error(f"Backup cleanup error: {str(e)}")
            return 0
    
    def _cleanup_s3_backups(self, cutoff_date):
        """Clean old backups from S3"""
        try:
            s3_client = boto3.client(
                's3',
                aws_access_key_id=self.aws_access_key,
                aws_secret_access_key=self.aws_secret_key,
                region_name=self.aws_region
            )
            
            removed_count = 0
            prefixes = ['database/', 'files/']
            
            for prefix in prefixes:
                response = s3_client.list_objects_v2(
                    Bucket=self.s3_bucket,
                    Prefix=prefix
                )
                
                if 'Contents' in response:
                    for obj in response['Contents']:
                        if obj['LastModified'].replace(tzinfo=None) < cutoff_date:
                            s3_client.delete_object(
                                Bucket=self.s3_bucket,
                                Key=obj['Key']
                            )
                            removed_count += 1
                            logger.info(f"Removed old S3 backup: {obj['Key']}")
            
            return removed_count
            
        except Exception as e:
            logger.error(f"S3 cleanup error: {str(e)}")
            return 0
    
    def restore_from_backup(self, backup_path, restore_type='database'):
        """Restore from backup file"""
        if not os.path.exists(backup_path):
            logger.error(f"Backup file not found: {backup_path}")
            return False
        
        try:
            if restore_type == 'database':
                return self._restore_database(backup_path)
            elif restore_type == 'files':
                return self._restore_files(backup_path)
            else:
                logger.error(f"Unknown restore type: {restore_type}")
                return False
                
        except Exception as e:
            logger.error(f"Restore error: {str(e)}")
            return False
    
    def _restore_database(self, backup_path):
        """Restore database from backup"""
        try:
            db_uri = current_app.config.get('SQLALCHEMY_DATABASE_URI')
            db_config = self._parse_db_uri(db_uri)
            
            if db_config['type'] == 'postgresql':
                return self._restore_postgresql(db_config, backup_path)
            elif db_config['type'] == 'sqlite':
                return self._restore_sqlite(db_config, backup_path)
            else:
                raise ValueError(f"Unsupported database type: {db_config['type']}")
                
        except Exception as e:
            logger.error(f"Database restore error: {str(e)}")
            return False
    
    def _restore_postgresql(self, db_config, backup_path):
        """Restore PostgreSQL database from backup"""
        try:
            # Set environment variables
            env = os.environ.copy()
            if db_config['password']:
                env['PGPASSWORD'] = db_config['password']
            
            # Decompress and restore
            cmd = [
                'psql',
                '-h', db_config['host'],
                '-p', db_config['port'],
                '-U', db_config['user'],
                '-d', db_config['database'],
                '--no-password'
            ]
            
            with gzip.open(backup_path, 'rb') as gz:
                process = subprocess.Popen(
                    cmd,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    env=env
                )
                
                stdout, stderr = process.communicate(input=gz.read())
            
            if process.returncode == 0:
                logger.info("PostgreSQL restore completed successfully")
                return True
            else:
                logger.error(f"PostgreSQL restore failed: {stderr.decode()}")
                return False
                
        except Exception as e:
            logger.error(f"PostgreSQL restore error: {str(e)}")
            return False
    
    def _restore_sqlite(self, db_config, backup_path):
        """Restore SQLite database from backup"""
        try:
            target_path = db_config['path']
            
            # Backup existing database
            if os.path.exists(target_path):
                backup_existing = f"{target_path}.backup_{int(datetime.now().timestamp())}"
                shutil.copy2(target_path, backup_existing)
                logger.info(f"Existing database backed up to: {backup_existing}")
            
            # Restore from compressed backup
            with gzip.open(backup_path, 'rb') as f_in:
                with open(target_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            logger.info("SQLite restore completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"SQLite restore error: {str(e)}")
            return False
    
    def _restore_files(self, backup_path):
        """Restore files from backup"""
        try:
            with tarfile.open(backup_path, 'r:gz') as tar:
                tar.extractall(path='/')
            
            logger.info("Files restore completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Files restore error: {str(e)}")
            return False
    
    def get_backup_status(self):
        """Get backup system status and metrics"""
        status = {
            'backup_dir': self.backup_dir,
            'backup_dir_exists': os.path.exists(self.backup_dir) if self.backup_dir else False,
            's3_configured': bool(self.s3_bucket and self.aws_access_key),
            'retention_days': self.retention_days,
            'local_backups': [],
            'disk_usage': None
        }
        
        try:
            # Get local backup info
            if os.path.exists(self.backup_dir):
                for filename in os.listdir(self.backup_dir):
                    if filename.startswith(('db_backup_', 'files_backup_')):
                        filepath = os.path.join(self.backup_dir, filename)
                        stat = os.stat(filepath)
                        status['local_backups'].append({
                            'filename': filename,
                            'size_bytes': stat.st_size,
                            'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                            'age_days': (datetime.now() - datetime.fromtimestamp(stat.st_mtime)).days
                        })
                
                # Sort by modification time (newest first)
                status['local_backups'].sort(key=lambda x: x['modified'], reverse=True)
            
            # Get disk usage for backup directory
            if self.backup_dir and os.path.exists(self.backup_dir):
                disk_usage = psutil.disk_usage(self.backup_dir)
                status['disk_usage'] = {
                    'total_bytes': disk_usage.total,
                    'used_bytes': disk_usage.used,
                    'free_bytes': disk_usage.free,
                    'free_percent': (disk_usage.free / disk_usage.total) * 100
                }
            
        except Exception as e:
            logger.error(f"Error getting backup status: {str(e)}")
            status['error'] = str(e)
        
        return status

def create_backup_script():
    """Create backup script for cron jobs"""
    script_content = '''#!/bin/bash
# Automated backup script for Short-Term Landlord application

# Set error handling
set -e

# Log file
LOG_FILE="/app/logs/backup.log"
mkdir -p "$(dirname "$LOG_FILE")"

# Function to log messages
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

log "Starting automated backup process"

# Navigate to application directory
cd /app

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run backup using Flask CLI or Python script
python3 -c "
from app import create_app
from app.utils.backup_manager import BackupManager

app = create_app()
with app.app_context():
    backup_manager = BackupManager()
    
    # Create database backup
    db_backup = backup_manager.create_database_backup()
    if db_backup:
        print(f'Database backup created: {db_backup}')
    else:
        print('Database backup failed')
        exit(1)
    
    # Create files backup
    files_backup = backup_manager.create_files_backup()
    if files_backup:
        print(f'Files backup created: {files_backup}')
    
    # Cleanup old backups
    removed = backup_manager.cleanup_old_backups()
    print(f'Cleaned up {removed} old backups')
"

log "Backup process completed"
'''
    
    script_path = '/app/scripts/backup.sh'
    os.makedirs('/app/scripts', exist_ok=True)
    
    with open(script_path, 'w') as f:
        f.write(script_content)
    
    # Make script executable
    os.chmod(script_path, 0o755)
    
    return script_path