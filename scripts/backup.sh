#!/bin/bash
# Automated backup script for Short-Term Landlord application

# Set error handling
set -e

# Environment variables with defaults
BACKUP_DIR=${BACKUP_DIR:-"/backups"}
LOG_FILE=${LOG_FILE:-"/app/logs/backup.log"}
POSTGRES_HOST=${POSTGRES_HOST:-"db"}
POSTGRES_PORT=${POSTGRES_PORT:-"5432"}
POSTGRES_USER=${POSTGRES_USER:-"postgres"}
POSTGRES_DB=${POSTGRES_DB:-"flask_app"}
RETENTION_DAYS=${BACKUP_RETENTION_DAYS:-"7"}

# Create directories
mkdir -p "$BACKUP_DIR" "$(dirname "$LOG_FILE")"

# Function to log messages
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Function to check if database is ready
wait_for_db() {
    log "Waiting for database to be ready..."
    for i in {1..30}; do
        if pg_isready -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" >/dev/null 2>&1; then
            log "Database is ready"
            return 0
        fi
        log "Database not ready, waiting... (attempt $i/30)"
        sleep 5
    done
    log "Database not ready after 30 attempts"
    return 1
}

# Function to create database backup
backup_database() {
    local timestamp=$(date '+%Y%m%d_%H%M%S')
    local backup_file="$BACKUP_DIR/db_backup_${timestamp}.sql.gz"
    
    log "Starting database backup: $backup_file"
    
    # Create database backup
    if PGPASSWORD="$POSTGRES_PASSWORD" pg_dump \
        -h "$POSTGRES_HOST" \
        -p "$POSTGRES_PORT" \
        -U "$POSTGRES_USER" \
        -d "$POSTGRES_DB" \
        --verbose \
        --clean \
        --if-exists \
        --create \
        --no-password | gzip > "$backup_file"; then
        
        # Verify backup file
        if [ -f "$backup_file" ] && [ -s "$backup_file" ]; then
            local file_size=$(du -h "$backup_file" | cut -f1)
            log "Database backup completed successfully: $backup_file ($file_size)"
            
            # Upload to S3 if configured
            if [ -n "$AWS_S3_BUCKET" ] && [ -n "$AWS_ACCESS_KEY_ID" ]; then
                upload_to_s3 "$backup_file" "database/$(basename "$backup_file")"
            fi
            
            return 0
        else
            log "ERROR: Backup file is empty or was not created"
            return 1
        fi
    else
        log "ERROR: Database backup failed"
        return 1
    fi
}

# Function to create files backup
backup_files() {
    local timestamp=$(date '+%Y%m%d_%H%M%S')
    local backup_file="$BACKUP_DIR/files_backup_${timestamp}.tar.gz"
    
    log "Starting files backup: $backup_file"
    
    # Paths to backup
    local paths_to_backup=""
    
    # Check if upload directory exists
    if [ -d "/app/uploads" ]; then
        paths_to_backup="$paths_to_backup /app/uploads"
    fi
    
    # Check if logs directory exists
    if [ -d "/app/logs" ]; then
        paths_to_backup="$paths_to_backup /app/logs"
    fi
    
    if [ -z "$paths_to_backup" ]; then
        log "No files to backup - upload and log directories not found"
        return 0
    fi
    
    # Create tar.gz backup
    if tar -czf "$backup_file" $paths_to_backup 2>/dev/null; then
        local file_size=$(du -h "$backup_file" | cut -f1)
        log "Files backup completed successfully: $backup_file ($file_size)"
        
        # Upload to S3 if configured
        if [ -n "$AWS_S3_BUCKET" ] && [ -n "$AWS_ACCESS_KEY_ID" ]; then
            upload_to_s3 "$backup_file" "files/$(basename "$backup_file")"
        fi
        
        return 0
    else
        log "ERROR: Files backup failed"
        return 1
    fi
}

# Function to upload to S3
upload_to_s3() {
    local local_file="$1"
    local s3_key="$2"
    
    log "Uploading to S3: s3://$AWS_S3_BUCKET/$s3_key"
    
    if aws s3 cp "$local_file" "s3://$AWS_S3_BUCKET/$s3_key" \
        --storage-class STANDARD_IA \
        --server-side-encryption AES256; then
        log "S3 upload completed successfully"
        return 0
    else
        log "ERROR: S3 upload failed"
        return 1
    fi
}

# Function to cleanup old backups
cleanup_old_backups() {
    log "Cleaning up backups older than $RETENTION_DAYS days"
    
    local removed_count=0
    
    # Clean local backups
    if [ -d "$BACKUP_DIR" ]; then
        # Find and remove old backup files
        while IFS= read -r -d '' file; do
            rm -f "$file"
            removed_count=$((removed_count + 1))
            log "Removed old backup: $(basename "$file")"
        done < <(find "$BACKUP_DIR" -name "*.sql.gz" -o -name "*.tar.gz" -mtime +$RETENTION_DAYS -print0 2>/dev/null)
    fi
    
    # Clean S3 backups if configured
    if [ -n "$AWS_S3_BUCKET" ] && [ -n "$AWS_ACCESS_KEY_ID" ]; then
        cleanup_s3_backups
    fi
    
    log "Cleanup completed: removed $removed_count local backups"
}

# Function to cleanup S3 backups
cleanup_s3_backups() {
    log "Cleaning up old S3 backups"
    
    local cutoff_date=$(date -d "$RETENTION_DAYS days ago" '+%Y-%m-%d')
    
    # List and delete old backups from S3
    for prefix in "database/" "files/"; do
        aws s3api list-objects-v2 \
            --bucket "$AWS_S3_BUCKET" \
            --prefix "$prefix" \
            --query "Contents[?LastModified<=\`$cutoff_date\`].Key" \
            --output text | while read -r key; do
            if [ -n "$key" ] && [ "$key" != "None" ]; then
                aws s3 rm "s3://$AWS_S3_BUCKET/$key"
                log "Removed old S3 backup: $key"
            fi
        done
    done
}

# Function to check disk space
check_disk_space() {
    local available_space=$(df "$BACKUP_DIR" | awk 'NR==2 {print $4}')
    local available_gb=$((available_space / 1024 / 1024))
    
    log "Available disk space: ${available_gb}GB"
    
    if [ "$available_gb" -lt 1 ]; then
        log "WARNING: Low disk space (less than 1GB available)"
        return 1
    fi
    
    return 0
}

# Function to send notification (if configured)
send_notification() {
    local status="$1"
    local message="$2"
    
    # You can implement notification logic here (email, Slack, etc.)
    log "NOTIFICATION [$status]: $message"
}

# Main backup function
main() {
    log "=== Starting backup process ==="
    log "Backup directory: $BACKUP_DIR"
    log "Retention period: $RETENTION_DAYS days"
    log "S3 bucket: ${AWS_S3_BUCKET:-"Not configured"}"
    
    local success=true
    
    # Check disk space
    if ! check_disk_space; then
        log "WARNING: Continuing with backup despite low disk space"
    fi
    
    # Wait for database
    if ! wait_for_db; then
        log "ERROR: Database not available"
        send_notification "ERROR" "Database backup failed - database not available"
        exit 1
    fi
    
    # Create database backup
    if ! backup_database; then
        log "ERROR: Database backup failed"
        send_notification "ERROR" "Database backup failed"
        success=false
    fi
    
    # Create files backup
    if ! backup_files; then
        log "ERROR: Files backup failed"
        send_notification "WARNING" "Files backup failed"
        # Don't fail the entire process for files backup
    fi
    
    # Cleanup old backups
    cleanup_old_backups
    
    # Final status
    if [ "$success" = true ]; then
        log "=== Backup process completed successfully ==="
        send_notification "SUCCESS" "Backup process completed successfully"
        exit 0
    else
        log "=== Backup process completed with errors ==="
        send_notification "ERROR" "Backup process completed with errors"
        exit 1
    fi
}

# Handle signals
trap 'log "Backup interrupted"; exit 130' INT TERM

# Run main function
main "$@"