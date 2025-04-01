import os
import uuid
import boto3
import magic
import subprocess
from flask import current_app
from werkzeug.utils import secure_filename
from app.models import StorageBackend

def allowed_file(filename, allowed_extensions):
    """Check if a file has an allowed extension"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def get_file_mime_type(file_storage):
    """Get the MIME type of a file using python-magic"""
    mime = magic.Magic(mime=True)
    return mime.from_buffer(file_storage.read(1024))

def generate_unique_filename(original_filename):
    """Generate a unique filename to prevent collisions"""
    filename = secure_filename(original_filename)
    unique_id = uuid.uuid4().hex
    return f"{unique_id}_{filename}"

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
    # Determine the upload directory
    base_path = current_app.config.get('LOCAL_STORAGE_PATH')
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
    mime = magic.Magic(mime=True)
    mime_type = mime.from_file(file_path)
    
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
    
    mime = magic.Magic(mime=True)
    mime_type = mime.from_buffer(file_storage.read(1024))
    file_storage.seek(0)
    
    # Return the S3 URL
    s3_url = f"https://{bucket_name}.s3.{region}.amazonaws.com/{s3_key}"
    
    return (s3_url, StorageBackend.S3, file_size, mime_type)

def save_file_to_rclone(file_storage, session_id, media_type, filename, is_start_video=None):
    """Save a file to a remote storage using rclone"""
    # Get rclone configuration
    remote = current_app.config.get('RCLONE_REMOTE')
    path = current_app.config.get('RCLONE_PATH')
    
    # Save file temporarily to local storage
    temp_dir = os.path.join(current_app.config.get('LOCAL_STORAGE_PATH'), 'temp')
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
    
    mime = magic.Magic(mime=True)
    mime_type = mime.from_buffer(file_storage.read(1024))
    
    # Return the remote path
    return (f"rclone://{remote}:{remote_file_path}", StorageBackend.RCLONE, file_size, mime_type)
