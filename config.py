import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    """Base configuration class"""
    # Security: SECRET_KEY must be set in environment - no fallback allowed
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if not SECRET_KEY:
        raise RuntimeError(
            "SECRET_KEY environment variable must be set!\n"
            "Generate a secure key with: python -c 'import secrets; print(secrets.token_hex(32))'"
        )
    
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Database connection pooling for production performance
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': int(os.environ.get('DB_POOL_SIZE', 10)),
        'max_overflow': int(os.environ.get('DB_MAX_OVERFLOW', 20)),
        'pool_pre_ping': True,
        'pool_recycle': int(os.environ.get('DB_POOL_RECYCLE', 3600)),
        'pool_timeout': int(os.environ.get('DB_POOL_TIMEOUT', 30)),
        'echo': os.environ.get('DB_ECHO', 'false').lower() == 'true'
    }
    
    # Redis configuration for caching and sessions
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    CACHE_TYPE = os.environ.get('CACHE_TYPE', 'simple')  # 'redis' for production
    CACHE_REDIS_URL = REDIS_URL
    CACHE_DEFAULT_TIMEOUT = int(os.environ.get('CACHE_DEFAULT_TIMEOUT', 300))
    
    # Session configuration
    SESSION_TYPE = os.environ.get('SESSION_TYPE', 'filesystem')  # 'redis' for production
    SESSION_REDIS_URL = REDIS_URL
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True
    SESSION_KEY_PREFIX = os.environ.get('SESSION_KEY_PREFIX', 'stll_session:')
    
    # Enhanced session security
    SESSION_COOKIE_SECURE = os.environ.get('FLASK_ENV') == 'production'  # HTTPS only in production
    SESSION_COOKIE_HTTPONLY = True  # Prevent XSS access to session cookie
    SESSION_COOKIE_SAMESITE = 'Lax'  # CSRF protection
    SESSION_COOKIE_NAME = 'stll_session'
    SESSION_COOKIE_DOMAIN = None  # Use default (current domain)
    
    # Performance settings
    SQLALCHEMY_RECORD_QUERIES = os.environ.get('SQLALCHEMY_RECORD_QUERIES', 'false').lower() == 'true'
    DATABASE_QUERY_TIMEOUT = int(os.environ.get('DATABASE_QUERY_TIMEOUT', 30))
    SLOW_QUERY_THRESHOLD = float(os.environ.get('SLOW_QUERY_THRESHOLD', 0.5))
    
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
    
    # Security settings
    WTF_CSRF_TIME_LIMIT = int(os.environ.get('CSRF_TIME_LIMIT', 3600))
    PERMANENT_SESSION_LIFETIME = int(os.environ.get('SESSION_LIFETIME', 1800))  # 30 minutes
    
    # Rate limiting
    RATELIMIT_STORAGE_URL = REDIS_URL
    RATELIMIT_STRATEGY = os.environ.get('RATELIMIT_STRATEGY', 'fixed-window')
    RATELIMIT_ENABLED = os.environ.get('RATELIMIT_ENABLED', 'true').lower() == 'true'
    
    # Logging configuration
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FORMAT = os.environ.get('LOG_FORMAT', 'structured')  # 'structured' or 'standard'
    
    # Monitoring and observability
    SENTRY_DSN = os.environ.get('SENTRY_DSN')
    PROMETHEUS_METRICS = os.environ.get('PROMETHEUS_METRICS', 'false').lower() == 'true'
    HEALTH_CHECK_ENABLED = os.environ.get('HEALTH_CHECK_ENABLED', 'true').lower() == 'true'
    
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
    
    # Override SQLAlchemy engine options for SQLite (no connection pooling)
    SQLALCHEMY_ENGINE_OPTIONS = {}
    
    # Disable caching and sessions for tests
    CACHE_TYPE = 'simple'
    SESSION_TYPE = 'filesystem'
    
    # Use a test server name for URL generation in tests
    SERVER_NAME = 'localhost:5000'
    
    # File upload configuration for tests
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # Disable caching and sessions for tests
    CACHE_TYPE = 'simple'
    SESSION_TYPE = 'filesystem'
    
    @classmethod
    def init_app(cls, app):
        # Make sure the test database is clean
        pass


class ProductionConfig(Config):
    """Production configuration with optimized settings"""
    DEBUG = False
    TESTING = False
    
    # Enable Redis for production
    CACHE_TYPE = 'redis'
    SESSION_TYPE = 'redis'
    
    # Enhanced database pooling for production
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': int(os.environ.get('DB_POOL_SIZE', 20)),
        'max_overflow': int(os.environ.get('DB_MAX_OVERFLOW', 30)),
        'pool_pre_ping': True,
        'pool_recycle': int(os.environ.get('DB_POOL_RECYCLE', 3600)),
        'pool_timeout': int(os.environ.get('DB_POOL_TIMEOUT', 30)),
        'echo': False  # Disable SQL echo in production
    }
    
    # Production security settings
    WTF_CSRF_TIME_LIMIT = 3600  # 1 hour
    PERMANENT_SESSION_LIFETIME = 1800  # 30 minutes
    
    # Force secure sessions in production
    SESSION_COOKIE_SECURE = True  # Always require HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Strict'  # Stricter in production
    
    # Enable all monitoring in production
    SQLALCHEMY_RECORD_QUERIES = True
    PROMETHEUS_METRICS = True
    HEALTH_CHECK_ENABLED = True
    
    # Production logging
    LOG_LEVEL = 'INFO'
    LOG_FORMAT = 'structured'
    
    # SSL and security headers
    SSL_REDIRECT = True
    PREFERRED_URL_SCHEME = 'https'
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        # Log to syslog in production
        import logging
        from logging.handlers import SysLogHandler
        syslog_handler = SysLogHandler()
        syslog_handler.setLevel(logging.WARNING)
        app.logger.addHandler(syslog_handler)


class StagingConfig(ProductionConfig):
    """Staging configuration - like production but with debug info"""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'
    
    # Smaller connection pools for staging
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 5,
        'max_overflow': 10,
        'pool_pre_ping': True,
        'pool_recycle': 3600,
        'pool_timeout': 30,
        'echo': False
    }


# AppEngine configuration that works with in-memory database
class AppEngineConfig(Config):
    """App Engine specific configuration"""
    DEBUG = False
    TESTING = False
    
    # Explicitly set secret key for session management
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'fallback-secret-key-for-appengine-' + 'ys-UAwX9cpR15q61xQMvDsv03KUvigYnLyv5rkOQZsg'
    
    # Use in-memory SQLite for App Engine
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'echo': False,
        'pool_pre_ping': True
    }
    
    # Disable features that require external services
    NOTIFICATION_EMAIL_ENABLED = False
    NOTIFICATION_SMS_ENABLED = False
    CACHE_TYPE = 'simple'
    SESSION_TYPE = 'simple'
    RATELIMIT_ENABLED = False
    
    # App Engine specific settings
    HEALTH_CHECK_ENABLED = True
    PROMETHEUS_METRICS = False
    
    # Enable CSRF protection for security
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600  # 1 hour
    # Use secure CSRF settings for serverless
    WTF_CSRF_SSL_STRICT = True  # Require HTTPS for CSRF tokens
    WTF_CSRF_CHECK_DEFAULT = True  # Check CSRF on all POST/PUT/DELETE requests

# Configuration mapping
config = {
    'development': Config,
    'testing': TestConfig,
    'staging': StagingConfig,
    'production': ProductionConfig,
    'appengine': AppEngineConfig,
    'default': Config
}