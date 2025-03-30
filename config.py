import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard-to-guess-string'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Email configuration for password reset
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')
    
    # Notification settings
    NOTIFICATION_EMAIL_ENABLED = os.environ.get('NOTIFICATION_EMAIL_ENABLED', 'True').lower() == 'true'
    NOTIFICATION_SMS_ENABLED = os.environ.get('NOTIFICATION_SMS_ENABLED', 'True').lower() == 'true'
    NOTIFICATION_REMINDER_HOURS = int(os.environ.get('NOTIFICATION_REMINDER_HOURS', 24))
    
    # Twilio SMS configuration
    TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
    TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
    TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER')
    
    # Admin user
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL')
    
    # Media storage configuration
    MEDIA_STORAGE_BACKEND = os.environ.get('MEDIA_STORAGE_BACKEND', 'local')  # local, s3, rclone
    
    # Local storage configuration
    LOCAL_STORAGE_PATH = os.environ.get('LOCAL_STORAGE_PATH') or os.path.join(basedir, 'app/static/uploads')
    
    # Amazon S3 configuration
    S3_BUCKET = os.environ.get('S3_BUCKET')
    S3_REGION = os.environ.get('S3_REGION', 'us-east-1')
    S3_ACCESS_KEY = os.environ.get('S3_ACCESS_KEY')
    S3_SECRET_KEY = os.environ.get('S3_SECRET_KEY')
    S3_PREFIX = os.environ.get('S3_PREFIX', 'cleaning-media')
    
    # Rclone configuration
    RCLONE_REMOTE = os.environ.get('RCLONE_REMOTE')
    RCLONE_PATH = os.environ.get('RCLONE_PATH')
    
    # Media upload limits
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH') or 50 * 1024 * 1024)  # 50MB default
    ALLOWED_PHOTO_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif'}
    ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'mov', 'avi', 'webm'}