"""
Configuration management service with intelligent fallback system.

This module provides a centralized configuration management system that:
1. Reads from environment variables (.env file) first
2. Falls back to database settings if not in environment
3. Provides default values as last resort
4. Allows admin configuration via web UI for non-sensitive settings
"""

import os
import json
from typing import Any, Optional, Dict, List
from flask import current_app, has_app_context
from app import db
from app.models import SiteSetting
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ConfigurationCategory:
    """Configuration categories for organizing settings"""
    SYSTEM = 'system'  # Read-only system settings from environment
    APPLICATION = 'application'  # General application settings
    FEATURES = 'features'  # Feature flags
    EMAIL = 'email'  # Email configuration
    SMS = 'sms'  # SMS/Twilio configuration
    STORAGE = 'storage'  # File storage settings
    SECURITY = 'security'  # Security settings
    INTEGRATION = 'integration'  # Third-party integrations
    PERFORMANCE = 'performance'  # Performance tuning


class ConfigurationType:
    """Configuration types for validation and display"""
    STRING = 'string'
    INTEGER = 'integer'
    FLOAT = 'float'
    BOOLEAN = 'boolean'
    JSON = 'json'
    PASSWORD = 'password'  # Masked in UI
    URL = 'url'
    EMAIL = 'email'
    PATH = 'path'


class ConfigurationItem:
    """Configuration item metadata"""
    def __init__(self, key: str, category: str, config_type: str, 
                 description: str, default_value: Any = None,
                 env_var: Optional[str] = None, sensitive: bool = False,
                 editable: bool = True, validation_rule: Optional[Dict] = None):
        self.key = key
        self.category = category
        self.config_type = config_type
        self.description = description
        self.default_value = default_value
        self.env_var = env_var or key.upper()
        self.sensitive = sensitive
        self.editable = editable and not sensitive  # Sensitive items not editable via UI
        self.validation_rule = validation_rule or {}


# Configuration registry - defines all available configurations
CONFIGURATION_REGISTRY = [
    # System Settings (Read-only from environment)
    ConfigurationItem(
        key='SECRET_KEY',
        category=ConfigurationCategory.SYSTEM,
        config_type=ConfigurationType.PASSWORD,
        description='Flask secret key for session encryption',
        sensitive=True,
        editable=False
    ),
    ConfigurationItem(
        key='DATABASE_URL',
        category=ConfigurationCategory.SYSTEM,
        config_type=ConfigurationType.URL,
        description='Database connection URL',
        default_value='sqlite:///app.db',
        sensitive=True,
        editable=False
    ),
    ConfigurationItem(
        key='BASE_URL',
        category=ConfigurationCategory.SYSTEM,
        config_type=ConfigurationType.URL,
        description='Base URL for the application',
        default_value='http://localhost:5001',
        editable=True
    ),
    
    # Application Settings
    ConfigurationItem(
        key='APP_NAME',
        category=ConfigurationCategory.APPLICATION,
        config_type=ConfigurationType.STRING,
        description='Application display name',
        default_value='Short Term Landlord',
        editable=True
    ),
    ConfigurationItem(
        key='MAX_PROPERTIES_PER_USER',
        category=ConfigurationCategory.APPLICATION,
        config_type=ConfigurationType.INTEGER,
        description='Maximum number of properties per user',
        default_value=10,
        editable=True,
        validation_rule={'min': 1, 'max': 100}
    ),
    ConfigurationItem(
        key='DEFAULT_TIMEZONE',
        category=ConfigurationCategory.APPLICATION,
        config_type=ConfigurationType.STRING,
        description='Default timezone for the application',
        default_value='America/New_York',
        editable=True
    ),
    
    # Feature Flags
    ConfigurationItem(
        key='ENABLE_GUEST_REVIEWS',
        category=ConfigurationCategory.FEATURES,
        config_type=ConfigurationType.BOOLEAN,
        description='Enable guest review functionality',
        default_value=True,
        env_var='FEATURE_GUEST_REVIEWS',
        editable=True
    ),
    ConfigurationItem(
        key='ENABLE_AI_FEATURES',
        category=ConfigurationCategory.FEATURES,
        config_type=ConfigurationType.BOOLEAN,
        description='Enable AI-powered features',
        default_value=False,
        env_var='FEATURE_AI',
        editable=True
    ),
    ConfigurationItem(
        key='ENABLE_SMS_NOTIFICATIONS',
        category=ConfigurationCategory.FEATURES,
        config_type=ConfigurationType.BOOLEAN,
        description='Enable SMS notifications',
        default_value=False,
        env_var='FEATURE_SMS',
        editable=True
    ),
    ConfigurationItem(
        key='ENABLE_FINANCIAL_ANALYTICS',
        category=ConfigurationCategory.FEATURES,
        config_type=ConfigurationType.BOOLEAN,
        description='Enable financial analytics dashboard',
        default_value=True,
        env_var='FEATURE_FINANCIAL_ANALYTICS',
        editable=True
    ),
    
    # Email Configuration
    ConfigurationItem(
        key='MAIL_SERVER',
        category=ConfigurationCategory.EMAIL,
        config_type=ConfigurationType.STRING,
        description='SMTP server hostname',
        editable=True
    ),
    ConfigurationItem(
        key='MAIL_PORT',
        category=ConfigurationCategory.EMAIL,
        config_type=ConfigurationType.INTEGER,
        description='SMTP server port',
        default_value=587,
        editable=True,
        validation_rule={'min': 1, 'max': 65535}
    ),
    ConfigurationItem(
        key='MAIL_USE_TLS',
        category=ConfigurationCategory.EMAIL,
        config_type=ConfigurationType.BOOLEAN,
        description='Use TLS for email',
        default_value=True,
        editable=True
    ),
    ConfigurationItem(
        key='MAIL_USERNAME',
        category=ConfigurationCategory.EMAIL,
        config_type=ConfigurationType.STRING,
        description='SMTP username',
        editable=True
    ),
    ConfigurationItem(
        key='MAIL_PASSWORD',
        category=ConfigurationCategory.EMAIL,
        config_type=ConfigurationType.PASSWORD,
        description='SMTP password',
        sensitive=True,
        editable=False
    ),
    ConfigurationItem(
        key='MAIL_DEFAULT_SENDER',
        category=ConfigurationCategory.EMAIL,
        config_type=ConfigurationType.EMAIL,
        description='Default sender email address',
        editable=True
    ),
    
    # SMS/Twilio Configuration
    ConfigurationItem(
        key='TWILIO_ACCOUNT_SID',
        category=ConfigurationCategory.SMS,
        config_type=ConfigurationType.PASSWORD,
        description='Twilio Account SID',
        sensitive=True,
        editable=False
    ),
    ConfigurationItem(
        key='TWILIO_AUTH_TOKEN',
        category=ConfigurationCategory.SMS,
        config_type=ConfigurationType.PASSWORD,
        description='Twilio Auth Token',
        sensitive=True,
        editable=False
    ),
    ConfigurationItem(
        key='TWILIO_PHONE_NUMBER',
        category=ConfigurationCategory.SMS,
        config_type=ConfigurationType.STRING,
        description='Twilio phone number',
        editable=True
    ),
    
    # Storage Configuration
    ConfigurationItem(
        key='MEDIA_STORAGE_BACKEND',
        category=ConfigurationCategory.STORAGE,
        config_type=ConfigurationType.STRING,
        description='Storage backend (local, s3, rclone)',
        default_value='local',
        editable=True,
        validation_rule={'choices': ['local', 's3', 'rclone']}
    ),
    ConfigurationItem(
        key='MAX_UPLOAD_SIZE',
        category=ConfigurationCategory.STORAGE,
        config_type=ConfigurationType.INTEGER,
        description='Maximum file upload size in MB',
        default_value=50,
        env_var='MAX_CONTENT_LENGTH',
        editable=True,
        validation_rule={'min': 1, 'max': 500}
    ),
    
    # Security Settings
    ConfigurationItem(
        key='SESSION_LIFETIME',
        category=ConfigurationCategory.SECURITY,
        config_type=ConfigurationType.INTEGER,
        description='Session lifetime in seconds',
        default_value=1800,
        editable=True,
        validation_rule={'min': 300, 'max': 86400}
    ),
    ConfigurationItem(
        key='PASSWORD_MIN_LENGTH',
        category=ConfigurationCategory.SECURITY,
        config_type=ConfigurationType.INTEGER,
        description='Minimum password length',
        default_value=8,
        editable=True,
        validation_rule={'min': 6, 'max': 32}
    ),
    ConfigurationItem(
        key='MAX_LOGIN_ATTEMPTS',
        category=ConfigurationCategory.SECURITY,
        config_type=ConfigurationType.INTEGER,
        description='Maximum login attempts before lockout',
        default_value=5,
        editable=True,
        validation_rule={'min': 3, 'max': 10}
    ),
    ConfigurationItem(
        key='ACCOUNT_LOCKOUT_DURATION',
        category=ConfigurationCategory.SECURITY,
        config_type=ConfigurationType.INTEGER,
        description='Account lockout duration in minutes',
        default_value=15,
        editable=True,
        validation_rule={'min': 5, 'max': 60}
    ),
    
    # Integration Settings
    ConfigurationItem(
        key='OPENAI_API_KEY',
        category=ConfigurationCategory.INTEGRATION,
        config_type=ConfigurationType.PASSWORD,
        description='OpenAI API key for AI features',
        sensitive=True,
        editable=False
    ),
    ConfigurationItem(
        key='GOOGLE_MAPS_API_KEY',
        category=ConfigurationCategory.INTEGRATION,
        config_type=ConfigurationType.PASSWORD,
        description='Google Maps API key',
        sensitive=True,
        editable=False
    ),
    
    # Performance Settings
    ConfigurationItem(
        key='CACHE_DEFAULT_TIMEOUT',
        category=ConfigurationCategory.PERFORMANCE,
        config_type=ConfigurationType.INTEGER,
        description='Default cache timeout in seconds',
        default_value=300,
        editable=True,
        validation_rule={'min': 0, 'max': 3600}
    ),
    ConfigurationItem(
        key='DB_POOL_SIZE',
        category=ConfigurationCategory.PERFORMANCE,
        config_type=ConfigurationType.INTEGER,
        description='Database connection pool size',
        default_value=10,
        editable=True,
        validation_rule={'min': 1, 'max': 50}
    ),
]


class ConfigurationService:
    """Service for managing application configuration"""
    
    def __init__(self):
        self._cache = {}
        self._registry = {item.key: item for item in CONFIGURATION_REGISTRY}
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value with intelligent fallback.
        
        Priority order:
        1. Environment variable
        2. Database setting
        3. Default value from registry
        4. Provided default value
        """
        # Check cache first
        if key in self._cache:
            return self._cache[key]
        
        # Get configuration item from registry
        config_item = self._registry.get(key)
        
        # 1. Check environment variable
        env_var = config_item.env_var if config_item else key.upper()
        env_value = os.environ.get(env_var)
        if env_value is not None:
            value = self._convert_value(env_value, config_item.config_type if config_item else None)
            self._cache[key] = value
            return value
        
        # 2. Check database setting (only for non-sensitive items and when in app context)
        if config_item and not config_item.sensitive and has_app_context():
            try:
                db_value = SiteSetting.get_setting(key)
                if db_value is not None:
                    value = self._convert_value(db_value, config_item.config_type)
                    self._cache[key] = value
                    return value
            except Exception as e:
                logger.debug(f"Could not get database setting for {key}: {e}")
        
        # 3. Use default from registry
        if config_item and config_item.default_value is not None:
            self._cache[key] = config_item.default_value
            return config_item.default_value
        
        # 4. Use provided default
        return default
    
    def set(self, key: str, value: Any, user_id: Optional[int] = None) -> bool:
        """
        Set configuration value in database.
        
        Only allows setting non-sensitive, editable configurations.
        """
        config_item = self._registry.get(key)
        
        # Check if item can be edited
        if not config_item:
            logger.warning(f"Attempted to set unknown configuration: {key}")
            return False
        
        if not config_item.editable:
            logger.warning(f"Attempted to edit non-editable configuration: {key}")
            return False
        
        # Validate value
        if not self._validate_value(value, config_item):
            logger.warning(f"Invalid value for configuration {key}: {value}")
            return False
        
        # Convert value to string for storage
        str_value = self._value_to_string(value, config_item.config_type)
        
        # Update in database
        try:
            SiteSetting.set_setting(
                key=key,
                value=str_value,
                description=config_item.description,
                visible=not config_item.sensitive
            )
            db.session.commit()
            
            # Clear cache
            if key in self._cache:
                del self._cache[key]
            
            # Log the change
            self._log_configuration_change(key, value, user_id)
            
            return True
        except Exception as e:
            logger.error(f"Failed to set configuration {key}: {e}")
            db.session.rollback()
            return False
    
    def get_all_by_category(self, category: Optional[str] = None) -> Dict[str, Dict]:
        """Get all configurations, optionally filtered by category"""
        result = {}
        
        for key, config_item in self._registry.items():
            if category and config_item.category != category:
                continue
            
            # Get current value
            value = self.get(key)
            
            # Mask sensitive values
            display_value = '********' if config_item.sensitive and value else value
            
            result[key] = {
                'value': value,
                'display_value': display_value,
                'category': config_item.category,
                'type': config_item.config_type,
                'description': config_item.description,
                'editable': config_item.editable,
                'sensitive': config_item.sensitive,
                'default': config_item.default_value,
                'validation': config_item.validation_rule,
                'from_env': os.environ.get(config_item.env_var) is not None
            }
        
        return result
    
    def get_categories(self) -> List[str]:
        """Get list of all configuration categories"""
        categories = set()
        for config_item in self._registry.values():
            categories.add(config_item.category)
        return sorted(list(categories))
    
    def _convert_value(self, value: str, config_type: Optional[str]) -> Any:
        """Convert string value to appropriate type"""
        if config_type == ConfigurationType.INTEGER:
            try:
                return int(value)
            except (ValueError, TypeError):
                return None
        elif config_type == ConfigurationType.FLOAT:
            try:
                return float(value)
            except (ValueError, TypeError):
                return None
        elif config_type == ConfigurationType.BOOLEAN:
            return value.lower() in ('true', '1', 'yes', 'on')
        elif config_type == ConfigurationType.JSON:
            try:
                return json.loads(value)
            except (ValueError, TypeError):
                return None
        else:
            return value
    
    def _value_to_string(self, value: Any, config_type: str) -> str:
        """Convert value to string for storage"""
        if config_type == ConfigurationType.BOOLEAN:
            return 'true' if value else 'false'
        elif config_type == ConfigurationType.JSON:
            return json.dumps(value)
        else:
            return str(value)
    
    def _validate_value(self, value: Any, config_item: ConfigurationItem) -> bool:
        """Validate configuration value against rules"""
        if not config_item.validation_rule:
            return True
        
        rules = config_item.validation_rule
        
        # Check min/max for numeric types
        if config_item.config_type in (ConfigurationType.INTEGER, ConfigurationType.FLOAT):
            if 'min' in rules and value < rules['min']:
                return False
            if 'max' in rules and value > rules['max']:
                return False
        
        # Check choices
        if 'choices' in rules and value not in rules['choices']:
            return False
        
        # Check string length
        if config_item.config_type == ConfigurationType.STRING:
            if 'min_length' in rules and len(value) < rules['min_length']:
                return False
            if 'max_length' in rules and len(value) > rules['max_length']:
                return False
        
        return True
    
    def _log_configuration_change(self, key: str, value: Any, user_id: Optional[int]):
        """Log configuration changes for audit trail"""
        # Don't log sensitive values
        config_item = self._registry.get(key)
        logged_value = '********' if config_item and config_item.sensitive else str(value)
        
        logger.info(f"Configuration changed: {key} = {logged_value} by user {user_id}")
        
        # TODO: Implement audit log model to store changes in database


# Global configuration service instance
config_service = ConfigurationService()