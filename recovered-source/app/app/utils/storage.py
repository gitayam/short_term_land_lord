import os
from werkzeug.utils import secure_filename
from flask import current_app
from app.models import MediaType, StorageBackend

def allowed_file(filename):
    """Check if the file extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def save_file_to_storage(file, property_id, media_type):
    """Save a file to the configured storage backend.
    
    Args:
        file: The file to save
        property_id: The ID of the property this file belongs to
        media_type: The type of media (from MediaType enum)
        
    Returns:
        tuple: (file_path, storage_backend, file_size, mime_type)
    """
    if not file or not allowed_file(file.filename):
        raise ValueError("Invalid file type")
    
    # Generate a unique filename
    filename = secure_filename(file.filename)
    unique_filename = f"{property_id}_{media_type.value}_{filename}"
    
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