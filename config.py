import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    """Base configuration class"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Database connection pooling and performance
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': int(os.environ.get('DB_POOL_SIZE', 10)),
        'max_overflow': int(os.environ.get('DB_MAX_OVERFLOW', 20)),
        'pool_pre_ping': True,
        'pool_recycle': int(os.environ.get('DB_POOL_RECYCLE', 3600)),
        'pool_timeout': int(os.environ.get('DB_POOL_TIMEOUT', 30)),
        'echo': os.environ.get('DB_ECHO', 'false').lower() == 'true'
    }
    
    # Database query optimization
    SQLALCHEMY_RECORD_QUERIES = os.environ.get('DB_RECORD_QUERIES', 'false').lower() == 'true'
    DATABASE_QUERY_TIMEOUT = int(os.environ.get('DB_QUERY_TIMEOUT', 30))
    
    # Base URL for webhooks and callbacks
    BASE_URL = os.environ.get('BASE_URL') or 'http://localhost:5001'
    
    # Email configuration for password reset
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')
    
    # Notification settings
    NOTIFICATION_EMAIL_ENABLED = True
    NOTIFICATION_SMS_ENABLED = True
    NOTIFICATION_REMINDER_HOURS = int(os.environ.get('NOTIFICATION_REMINDER_HOURS', 24))
    
    # Twilio SMS configuration
    TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
    TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
    TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER')
    
    # Admin user
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL')
    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD')
    ADMIN_FIRST_NAME = os.environ.get('ADMIN_FIRST_NAME', 'System')
    ADMIN_LAST_NAME = os.environ.get('ADMIN_LAST_NAME', 'Administrator')
    
    # Authentication settings
    AUTH_USE_SSO = os.environ.get('AUTH_USE_SSO', 'true').lower() == 'true'
    AUTH_USE_LOCAL = os.environ.get('AUTH_USE_LOCAL', 'true').lower() == 'true'
    
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
    try:
        # Try to get MAX_CONTENT_LENGTH from environment
        max_content_env = os.environ.get('MAX_CONTENT_LENGTH')
        if max_content_env:
            # Strip any comments or extra text
            max_content_env = max_content_env.split('#')[0].strip()
            MAX_CONTENT_LENGTH = int(max_content_env)
        else:
            # Default: 50MB
            MAX_CONTENT_LENGTH = 50 * 1024 * 1024
    except (ValueError, TypeError):
        # Fallback to default if conversion fails
        MAX_CONTENT_LENGTH = 50 * 1024 * 1024
    ALLOWED_PHOTO_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif'}
    ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'mov', 'avi', 'webm'}
    
    # Redis configuration
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    CACHE_TYPE = os.environ.get('CACHE_TYPE', 'redis')
    CACHE_REDIS_URL = REDIS_URL
    CACHE_DEFAULT_TIMEOUT = int(os.environ.get('CACHE_DEFAULT_TIMEOUT', 300))
    
    # Session storage
    SESSION_TYPE = os.environ.get('SESSION_TYPE', 'redis')
    SESSION_REDIS_URL = REDIS_URL
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True
    SESSION_KEY_PREFIX = 'stll_session:'
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'false').lower() == 'true'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Additional configuration
    ADMINS = ['admin@shortermlandlord.com']
    REQUIRE_CLEANING_VIDEOS = False

class TestConfig(Config):
    """Test configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    NOTIFICATION_EMAIL_ENABLED = False
    NOTIFICATION_SMS_ENABLED = False
    USER_TABLE_NAME = 'user'  # For testing with the legacy schema
    
    # Use a test server name for URL generation in tests
    SERVER_NAME = 'localhost:5000'
    
    # File upload configuration for tests
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    @classmethod
    def init_app(cls, app):
        # Make sure the test database is clean
        with app.app_context():
            db.create_all()

class ProductionConfig(Config):
    """Production configuration with enhanced performance and security"""
    DEBUG = False
    TESTING = False
    
    # Enhanced database configuration for production
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': int(os.environ.get('DB_POOL_SIZE', 20)),
        'max_overflow': int(os.environ.get('DB_MAX_OVERFLOW', 30)),
        'pool_pre_ping': True,
        'pool_recycle': int(os.environ.get('DB_POOL_RECYCLE', 3600)),
        'pool_timeout': int(os.environ.get('DB_POOL_TIMEOUT', 30)),
        'echo': False
    }
    
    # Security configuration
    WTF_CSRF_TIME_LIMIT = 3600
    PERMANENT_SESSION_LIFETIME = 1800  # 30 minutes
    
    # SSL configuration
    SSL_REDIRECT = os.environ.get('SSL_REDIRECT', 'true').lower() == 'true'
    SSL_CERT_PATH = os.environ.get('SSL_CERT_PATH')
    SSL_KEY_PATH = os.environ.get('SSL_KEY_PATH')
    
    # Logging configuration
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.environ.get('LOG_FILE', '/app/logs/app.log')
    
    # External services
    SENTRY_DSN = os.environ.get('SENTRY_DSN')
    
    # Rate limiting
    RATELIMIT_STORAGE_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/1')
    RATELIMIT_STRATEGY = 'fixed-window'
    
    # Monitoring
    PROMETHEUS_METRICS = os.environ.get('PROMETHEUS_METRICS', 'true').lower() == 'true'
    HEALTH_CHECK_ENABLED = os.environ.get('HEALTH_CHECK_ENABLED', 'true').lower() == 'true'

class StagingConfig(ProductionConfig):
    """Staging configuration"""
    DEBUG = True
    TESTING = False
    LOG_LEVEL = 'DEBUG'

# Configuration mapping
config = {
    'development': Config,
    'testing': TestConfig,
    'staging': StagingConfig,
    'production': ProductionConfig,
    'default': Config
}