"""
PostgreSQL Configuration for Production
Supports both local development and Cloud SQL deployment
"""

import os
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))

class PostgreSQLConfig:
    """Base PostgreSQL configuration"""
    # Core Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # PostgreSQL Database Configuration
    # Format: postgresql://username:password@host:port/database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'postgresql://landlord:password@localhost:5432/short_term_landlord'
    
    # Cloud SQL Connection (for App Engine/Cloud Run)
    if os.environ.get('GAE_ENV') == 'standard':
        # Running on Google App Engine
        db_user = os.environ.get('DB_USER', 'landlord')
        db_pass = os.environ.get('DB_PASS', 'password')
        db_name = os.environ.get('DB_NAME', 'landlord_prod')
        cloud_sql_connection = os.environ.get('CLOUD_SQL_CONNECTION_NAME')
        
        if cloud_sql_connection:
            SQLALCHEMY_DATABASE_URI = f"postgresql+psycopg2://{db_user}:{db_pass}@/{db_name}?host=/cloudsql/{cloud_sql_connection}"
    
    # SQLAlchemy settings optimized for PostgreSQL
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True,
        'max_overflow': 20,
        'echo_pool': False
    }
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_RECORD_QUERIES = True
    
    # Performance settings
    DATABASE_QUERY_TIMEOUT = 30
    SLOW_QUERY_THRESHOLD = 0.5  # Log queries slower than 500ms
    
    # Session configuration
    SESSION_TYPE = 'sqlalchemy'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Cache configuration (use Redis if available)
    CACHE_TYPE = os.environ.get('CACHE_TYPE', 'redis')
    CACHE_REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    CACHE_DEFAULT_TIMEOUT = 300
    
    # Security
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None

class DevelopmentPostgreSQLConfig(PostgreSQLConfig):
    """Development configuration with local PostgreSQL"""
    DEBUG = True
    TESTING = False
    
    # Local PostgreSQL (Docker or native)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'postgresql://landlord:password@localhost:5432/landlord_dev'
    
    # Show SQL queries in development
    SQLALCHEMY_ECHO = True
    
    # Simplified cache for development
    CACHE_TYPE = 'simple'

class ProductionPostgreSQLConfig(PostgreSQLConfig):
    """Production configuration with Cloud SQL PostgreSQL"""
    DEBUG = False
    TESTING = False
    
    # Security headers
    SECURITY_HEADERS = {
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Content-Security-Policy': "default-src 'self'"
    }
    
    # Production logging
    LOG_LEVEL = 'INFO'
    LOG_TO_STDOUT = True

class TestPostgreSQLConfig(PostgreSQLConfig):
    """Test configuration with separate test database"""
    TESTING = True
    DEBUG = True
    
    # Use separate test database
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
        'postgresql://landlord:password@localhost:5432/landlord_test'
    
    # Disable CSRF for testing
    WTF_CSRF_ENABLED = False
    
    # Use simple cache for tests
    CACHE_TYPE = 'simple'

# Configuration dictionary
postgres_config = {
    'development': DevelopmentPostgreSQLConfig,
    'production': ProductionPostgreSQLConfig,
    'testing': TestPostgreSQLConfig,
    'default': DevelopmentPostgreSQLConfig
}