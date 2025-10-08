import os
import uuid
import boto3
try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    magic = None
    MAGIC_AVAILABLE = False
import subprocess
from flask import current_app
from werkzeug.utils import secure_filename
from app.models import StorageBackend

def allowed_file(filename, allowed_extensions):
    """Check if a file has an allowed extension"""
    if not filename or '.' not in filename:
        return False
    extension = filename.rsplit('.', 1)[1].lower()
    return extension in allowed_extensions

def get_file_mime_type(file_storage):
    """Get the MIME type of a file using python-magic"""
    if not MAGIC_AVAILABLE:
        return 'application/octet-stream'  # Default fallback
    
    # Save current position
    current_position = file_storage.stream.tell()
    file_storage.stream.seek(0)
    
    try:
        mime = magic.Magic(mime=True)
        file_header = file_storage.stream.read(1024)
        mime_type = mime.from_buffer(file_header)
        return mime_type
    finally:
        # Restore position
        file_storage.stream.seek(current_position)

def generate_unique_filename(original_filename):
    """Generate a secure unique filename to prevent collisions"""
    # Sanitize the original filename
    if not original_filename:
        original_filename = 'unnamed_file'
    
    filename = secure_filename(original_filename)
    
    # Extract extension safely
    if '.' in filename:
        extension = filename.rsplit('.', 1)[1].lower()
    else:
        extension = 'bin'  # Default extension
    
    # Generate unique filename with only the extension
    unique_id = uuid.uuid4().hex
    return f"{unique_id}.{extension}"

def validate_file_security(file_storage, allowed_extensions, max_size_mb=10):
    """Comprehensive file security validation"""
    if not file_storage or not file_storage.filename:
        raise ValueError("No file provided")
    
    # Check file extension
    if not allowed_file(file_storage.filename, allowed_extensions):
        raise ValueError(f"Invalid file extension. Allowed: {', '.join(allowed_extensions)}")
    
    # Check file size
    file_storage.stream.seek(0, 2)  # Seek to end
    file_size = file_storage.stream.tell()
    file_storage.stream.seek(0)  # Reset to beginning
    
    max_size = max_size_mb * 1024 * 1024  # Convert to bytes
    if file_size > max_size:
        raise ValueError(f"File too large. Maximum size: {max_size_mb}MB")
    
    # Validate MIME type if magic is available
    if MAGIC_AVAILABLE:
        detected_mime = get_file_mime_type(file_storage)
        
        # Define allowed MIME types based on extension
        allowed_mimes = {
            'jpg': ['image/jpeg'],
            'jpeg': ['image/jpeg'], 
            'png': ['image/png'],
            'gif': ['image/gif'],
            'mp4': ['video/mp4'],
            'mov': ['video/quicktime'],
            'avi': ['video/x-msvideo'],
            'pdf': ['application/pdf'],
            'txt': ['text/plain'],
            'csv': ['text/csv', 'text/plain']
        }
        
        extension = file_storage.filename.rsplit('.', 1)[1].lower()
        expected_mimes = allowed_mimes.get(extension, [])
        
        if expected_mimes and detected_mime not in expected_mimes:
            raise ValueError(f"File content doesn't match extension. Expected: {expected_mimes}, Got: {detected_mime}")
    
    return True

def save_file_to_storage(file_storage, session_id, media_type, is_start_video=None):
    """
    Save a file to the configured storage backend
    
    Args:
        file_storage: The uploaded file from the request
        session_id: The ID of the cleaning session
        media_type: The type of media (photo or video)
        is_start_video: For videos, whether this is a start or end video
        
    Returns:
        tuple: (file_path, storage_backend, file_size, mime_type)
    """
    # Get the storage backend from config
    storage_backend = current_app.config.get('MEDIA_STORAGE_BACKEND', 'local')
    
    # Generate a unique filename
    original_filename = file_storage.filename
    unique_filename = generate_unique_filename(original_filename)
    
    # Get file size and MIME type
    file_storage.seek(0, os.SEEK_END)
    file_size = file_storage.tell()
    file_storage.seek(0)
    
    mime_type = get_file_mime_type(file_storage)
    file_storage.seek(0)  # Reset file pointer after reading MIME type
    
    # Save the file based on the configured storage backend
    if storage_backend == 'local' or storage_backend == StorageBackend.LOCAL.value:
        return save_file_locally(file_storage, session_id, media_type, unique_filename, is_start_video)
    elif storage_backend == 's3' or storage_backend == StorageBackend.S3.value:
        return save_file_to_s3(file_storage, session_id, media_type, unique_filename, is_start_video)
    elif storage_backend == 'rclone' or storage_backend == StorageBackend.RCLONE.value:
        return save_file_to_rclone(file_storage, session_id, media_type, unique_filename, is_start_video)
    else:
        # Default to local storage if backend is not recognized
        return save_file_locally(file_storage, session_id, media_type, unique_filename, is_start_video)

def save_file_locally(file_storage, session_id, media_type, filename, is_start_video=None):
    """Save a file to local storage"""
    # Determine the upload directory with a default value
    base_path = current_app.config.get('LOCAL_STORAGE_PATH', 'static/uploads')
    
    # Ensure the base path exists
    if not os.path.exists(base_path):
        os.makedirs(base_path, exist_ok=True)
    
    media_type_folder = 'videos' if media_type.value == 'video' else 'photos'
    
    # Create directory structure: uploads/cleaning_sessions/{session_id}/{media_type}/
    upload_dir = os.path.join(base_path, 'cleaning_sessions', str(session_id), media_type_folder)
    os.makedirs(upload_dir, exist_ok=True)
    
    # For videos, add start or end subdirectory
    if media_type.value == 'video' and is_start_video is not None:
        video_type = 'start' if is_start_video else 'end'
        upload_dir = os.path.join(upload_dir, video_type)
        os.makedirs(upload_dir, exist_ok=True)
    
    # Save the file
    file_path = os.path.join(upload_dir, filename)
    file_storage.save(file_path)
    
    # Return the relative path for storage in the database
    relative_path = os.path.join('/static/uploads/cleaning_sessions', str(session_id), 
                                media_type_folder)
    if media_type.value == 'video' and is_start_video is not None:
        relative_path = os.path.join(relative_path, 'start' if is_start_video else 'end')
    
    relative_path = os.path.join(relative_path, filename)
    
    # Get file size and MIME type
    file_size = os.path.getsize(file_path)
    if MAGIC_AVAILABLE:
        mime = magic.Magic(mime=True)
        mime_type = mime.from_file(file_path)
    else:
        mime_type = 'application/octet-stream'
    
    return (relative_path, StorageBackend.LOCAL, file_size, mime_type)

def save_file_to_s3(file_storage, session_id, media_type, filename, is_start_video=None):
    """Save a file to Amazon S3"""
    # Get S3 configuration
    bucket_name = current_app.config.get('S3_BUCKET')
    region = current_app.config.get('S3_REGION')
    access_key = current_app.config.get('S3_ACCESS_KEY')
    secret_key = current_app.config.get('S3_SECRET_KEY')
    prefix = current_app.config.get('S3_PREFIX')
    
    # Create S3 client
    s3_client = boto3.client(
        's3',
        region_name=region,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key
    )
    
    # Determine the S3 key (path)
    media_type_folder = 'videos' if media_type.value == 'video' else 'photos'
    s3_key = f"{prefix}/cleaning_sessions/{session_id}/{media_type_folder}"
    
    # For videos, add start or end subdirectory
    if media_type.value == 'video' and is_start_video is not None:
        video_type = 'start' if is_start_video else 'end'
        s3_key = f"{s3_key}/{video_type}"
    
    s3_key = f"{s3_key}/{filename}"
    
    # Upload the file to S3
    s3_client.upload_fileobj(file_storage, bucket_name, s3_key)
    
    # Get file size and MIME type
    file_storage.seek(0, os.SEEK_END)
    file_size = file_storage.tell()
    file_storage.seek(0)
    
    if MAGIC_AVAILABLE:
        mime = magic.Magic(mime=True)
        mime_type = mime.from_buffer(file_storage.read(1024))
        file_storage.seek(0)
    else:
        mime_type = 'application/octet-stream'
    
    # Return the S3 URL
    s3_url = f"https://{bucket_name}.s3.{region}.amazonaws.com/{s3_key}"
    
    return (s3_url, StorageBackend.S3, file_size, mime_type)

def save_file_to_rclone(file_storage, session_id, media_type, filename, is_start_video=None):
    """Save a file to a remote storage using rclone"""
    # Get rclone configuration
    remote = current_app.config.get('RCLONE_REMOTE')
    path = current_app.config.get('RCLONE_PATH')
    
    # Save file temporarily to local storage with a default path
    temp_dir = os.path.join(current_app.config.get('LOCAL_STORAGE_PATH', 'static/uploads'), 'temp')
    os.makedirs(temp_dir, exist_ok=True)
    temp_path = os.path.join(temp_dir, filename)
    file_storage.save(temp_path)
    
    # Determine the remote path
    media_type_folder = 'videos' if media_type.value == 'video' else 'photos'
    remote_path = f"{path}/cleaning_sessions/{session_id}/{media_type_folder}"
    
    # For videos, add start or end subdirectory
    if media_type.value == 'video' and is_start_video is not None:
        video_type = 'start' if is_start_video else 'end'
        remote_path = f"{remote_path}/{video_type}"
    
    # Create the remote directory
    subprocess.run(['rclone', 'mkdir', f"{remote}:{remote_path}"])
    
    # Upload the file using rclone
    remote_file_path = f"{remote_path}/{filename}"
    subprocess.run(['rclone', 'copy', temp_path, f"{remote}:{remote_path}"])
    
    # Clean up the temporary file
    os.remove(temp_path)
    
    # Get file size and MIME type
    file_storage.seek(0, os.SEEK_END)
    file_size = file_storage.tell()
    file_storage.seek(0)
    
    if MAGIC_AVAILABLE:
        mime = magic.Magic(mime=True)
        mime_type = mime.from_buffer(file_storage.read(1024))
    else:
        mime_type = 'application/octet-stream'
    
    # Return the remote path
    return (f"rclone://{remote}:{remote_file_path}", StorageBackend.RCLONE, file_size, mime_type)