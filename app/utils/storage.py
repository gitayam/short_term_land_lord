import os
import magic
import uuid
from werkzeug.utils import secure_filename
from flask import current_app
from app.models import MediaType, StorageBackend

def allowed_file(filename):
    """Check if the file extension is allowed."""
    if not filename or '.' not in filename:
        return False
    
    extension = filename.rsplit('.', 1)[1].lower()
    allowed_extensions = current_app.config.get('ALLOWED_EXTENSIONS', [])
    return extension in allowed_extensions

def validate_file_content(file):
    """Validate file content using magic numbers."""
    # Read first 1024 bytes for magic number detection
    file.stream.seek(0)
    file_header = file.stream.read(1024)
    file.stream.seek(0)
    
    # Use python-magic to detect actual file type
    try:
        file_type = magic.from_buffer(file_header, mime=True)
        
        # Define allowed MIME types
        allowed_mime_types = {
            'image/jpeg',
            'image/png', 
            'image/gif',
            'image/webp',
            'video/mp4',
            'video/mov',
            'video/avi',
            'application/pdf',
            'text/plain',
            'text/csv'
        }
        
        return file_type in allowed_mime_types
    except Exception:
        return False

def save_file_to_storage(file, property_id, media_type):
    """Save a file to the configured storage backend.
    
    Args:
        file: The file to save
        property_id: The ID of the property this file belongs to
        media_type: The type of media (from MediaType enum)
        
    Returns:
        tuple: (file_path, storage_backend, file_size, mime_type)
    """
    if not file or not file.filename:
        raise ValueError("No file provided")
    
    # Validate file extension
    if not allowed_file(file.filename):
        raise ValueError("Invalid file extension")
    
    # Validate file content
    if not validate_file_content(file):
        raise ValueError("Invalid file content - file type mismatch")
    
    # Check file size (max 10MB)
    max_size = current_app.config.get('MAX_FILE_SIZE', 10 * 1024 * 1024)
    file.stream.seek(0, 2)  # Seek to end
    file_size = file.stream.tell()
    file.stream.seek(0)  # Reset to beginning
    
    if file_size > max_size:
        raise ValueError(f"File too large. Maximum size: {max_size} bytes")
    
    # Generate a secure unique filename
    original_filename = secure_filename(file.filename)
    extension = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else ''
    unique_filename = f"{property_id}_{media_type.value}_{uuid.uuid4().hex}.{extension}"
    
    # Get storage backend from config
    storage_backend = current_app.config.get('STORAGE_BACKEND', StorageBackend.LOCAL)
    
    if storage_backend == StorageBackend.LOCAL:
        return save_file_locally(file, unique_filename, media_type)
    elif storage_backend == StorageBackend.S3:
        return save_file_to_s3(file, unique_filename, media_type)
    elif storage_backend == StorageBackend.RCLONE:
        return save_file_with_rclone(file, unique_filename, media_type)
    else:
        raise ValueError(f"Unsupported storage backend: {storage_backend}")

def save_file_locally(file, filename, media_type):
    """Save a file to local storage.
    
    Args:
        file: The file to save
        filename: The filename to use
        media_type: The type of media
        
    Returns:
        tuple: (file_path, storage_backend, file_size, mime_type)
    """
    # Create upload directory if it doesn't exist
    upload_dir = os.path.join(current_app.config['LOCAL_STORAGE_PATH'], media_type.value)
    os.makedirs(upload_dir, exist_ok=True)
    
    # Save the file
    file_path = os.path.join(upload_dir, filename)
    file.save(file_path)
    
    # Get file info
    file_size = os.path.getsize(file_path)
    mime_type = file.content_type
    
    return file_path, StorageBackend.LOCAL, file_size, mime_type

def save_file_to_s3(file, filename, media_type):
    """Save a file to S3 storage.
    
    Args:
        file: The file to save
        filename: The filename to use
        media_type: The type of media
        
    Returns:
        tuple: (file_path, storage_backend, file_size, mime_type)
    """
    # This is a placeholder - implement actual S3 upload logic
    raise NotImplementedError("S3 storage not implemented yet")

def save_file_with_rclone(file, filename, media_type):
    """Save a file using rclone.
    
    Args:
        file: The file to save
        filename: The filename to use
        media_type: The type of media
        
    Returns:
        tuple: (file_path, storage_backend, file_size, mime_type)
    """
    # This is a placeholder - implement actual rclone upload logic
    raise NotImplementedError("Rclone storage not implemented yet") 