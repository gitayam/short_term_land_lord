"""
Enhanced Validation Utilities for Input Sanitization and Security

This module provides comprehensive input validation, XSS prevention,
SQL injection protection, and request validation decorators.
"""
import re
import html
import bleach
from typing import Optional, Union, List, Dict, Any
from flask import current_app, request, abort
from werkzeug.utils import secure_filename
import phonenumbers
from phonenumbers import NumberParseException
from marshmallow import Schema, fields, validate, ValidationError as MarshmallowValidationError, pre_load, post_load
from functools import wraps
import logging
from datetime import datetime
from email_validator import validate_email as validate_email_lib, EmailNotValidError


class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass


def sanitize_html(text: str, allowed_tags: Optional[List[str]] = None) -> str:
    """
    Sanitize HTML content to prevent XSS attacks
    
    Args:
        text: Raw HTML text
        allowed_tags: List of allowed HTML tags (default: safe tags only)
    
    Returns:
        Sanitized HTML string
    """
    if not text:
        return ""
    
    if allowed_tags is None:
        allowed_tags = ['p', 'br', 'strong', 'em', 'ul', 'ol', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']
    
    allowed_attributes = {
        '*': ['class'],
        'a': ['href', 'title'],
        'img': ['src', 'alt', 'width', 'height'],
    }
    
    return bleach.clean(
        text,
        tags=allowed_tags,
        attributes=allowed_attributes,
        strip=True
    )


def validate_email(email: str) -> bool:
    """
    Validate email address format
    
    Args:
        email: Email address to validate
    
    Returns:
        True if valid, False otherwise
    """
    if not email or not isinstance(email, str):
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email.strip().lower()))


def validate_phone_number(phone: str, country_code: str = 'US') -> Optional[str]:
    """
    Validate and format phone number
    
    Args:
        phone: Phone number string
        country_code: ISO country code for parsing
    
    Returns:
        Formatted phone number in E.164 format or None if invalid
    """
    if not phone:
        return None
    
    try:
        parsed = phonenumbers.parse(phone, country_code)
        if phonenumbers.is_valid_number(parsed):
            return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
    except NumberParseException:
        pass
    
    return None


def validate_password_strength(password: str) -> Dict[str, Any]:
    """
    Validate password strength
    
    Args:
        password: Password to validate
    
    Returns:
        Dictionary with validation results
    """
    if not password:
        return {
            'valid': False,
            'score': 0,
            'errors': ['Password is required']
        }
    
    errors = []
    score = 0
    
    # Length check
    if len(password) < 8:
        errors.append('Password must be at least 8 characters long')
    else:
        score += 1
    
    # Character variety checks
    if re.search(r'[a-z]', password):
        score += 1
    else:
        errors.append('Password must contain lowercase letters')
    
    if re.search(r'[A-Z]', password):
        score += 1
    else:
        errors.append('Password must contain uppercase letters')
    
    if re.search(r'\d', password):
        score += 1
    else:
        errors.append('Password must contain numbers')
    
    if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        score += 1
    else:
        errors.append('Password must contain special characters')
    
    # Common password check
    common_passwords = ['password', '123456', 'password123', 'admin', 'qwerty']
    if password.lower() in common_passwords:
        errors.append('Password is too common')
        score = max(0, score - 2)
    
    return {
        'valid': len(errors) == 0,
        'score': min(score, 5),
        'errors': errors
    }


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename for safe storage
    
    Args:
        filename: Original filename
    
    Returns:
        Sanitized filename
    """
    if not filename:
        return "unnamed_file"
    
    # Use werkzeug's secure_filename and add additional sanitization
    safe_name = secure_filename(filename)
    
    # Remove any remaining problematic characters
    safe_name = re.sub(r'[^\w\-_\.]', '_', safe_name)
    
    # Ensure filename isn't too long
    if len(safe_name) > 100:
        name, ext = safe_name.rsplit('.', 1) if '.' in safe_name else (safe_name, '')
        safe_name = name[:90] + ('.' + ext if ext else '')
    
    return safe_name or "unnamed_file"


def validate_url(url: str) -> bool:
    """
    Validate URL format
    
    Args:
        url: URL to validate
    
    Returns:
        True if valid, False otherwise
    """
    if not url:
        return False
    
    pattern = r'^https?:\/\/(?:[-\w.])+(?:\:[0-9]+)?(?:\/(?:[\w\/_.])*(?:\?(?:[\w&=%.])*)?(?:\#(?:[\w.])*)?)?$'
    return bool(re.match(pattern, url))


def validate_positive_number(value: Union[str, int, float], allow_zero: bool = False) -> bool:
    """
    Validate that a value is a positive number
    
    Args:
        value: Value to validate
        allow_zero: Whether zero is considered valid
    
    Returns:
        True if valid, False otherwise
    """
    try:
        num = float(value)
        return num >= 0 if allow_zero else num > 0
    except (ValueError, TypeError):
        return False


def sanitize_text_input(text: str, max_length: Optional[int] = None) -> str:
    """
    Sanitize text input by removing dangerous characters
    
    Args:
        text: Text to sanitize
        max_length: Maximum allowed length
    
    Returns:
        Sanitized text
    """
    if not text:
        return ""
    
    # Remove null bytes and control characters except newlines and tabs
    sanitized = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
    
    # Normalize whitespace
    sanitized = re.sub(r'\s+', ' ', sanitized).strip()
    
    # Truncate if needed
    if max_length and len(sanitized) > max_length:
        sanitized = sanitized[:max_length].strip()
    
    return sanitized


def validate_enum_value(value: str, enum_class) -> bool:
    """
    Validate that a value is a valid enum member
    
    Args:
        value: Value to validate
        enum_class: Enum class to check against
    
    Returns:
        True if valid, False otherwise
    """
    try:
        enum_class(value)
        return True
    except (ValueError, TypeError):
        return False


def validate_coordinate(coord: Union[str, float]) -> bool:
    """
    Validate latitude/longitude coordinate
    
    Args:
        coord: Coordinate value
    
    Returns:
        True if valid, False otherwise
    """
    try:
        num = float(coord)
        return -180 <= num <= 180
    except (ValueError, TypeError):
        return False


def validate_json_string(json_str: str) -> bool:
    """
    Validate that a string is valid JSON
    
    Args:
        json_str: JSON string to validate
    
    Returns:
        True if valid, False otherwise
    """
    if not json_str:
        return False
    
    try:
        import json
        json.loads(json_str)
        return True
    except json.JSONDecodeError:
        return False


class InputValidator:
    """
    Class-based validator for complex validation scenarios
    """
    
    def __init__(self):
        self.errors = []
    
    def add_error(self, field: str, message: str) -> None:
        """Add validation error"""
        self.errors.append({'field': field, 'message': message})
    
    def validate_required(self, value: Any, field_name: str) -> bool:
        """Validate required field"""
        if not value or (isinstance(value, str) and not value.strip()):
            self.add_error(field_name, f'{field_name} is required')
            return False
        return True
    
    def validate_string_length(self, value: str, field_name: str, 
                             min_length: int = 0, max_length: int = None) -> bool:
        """Validate string length"""
        if not isinstance(value, str):
            self.add_error(field_name, f'{field_name} must be a string')
            return False
        
        if len(value) < min_length:
            self.add_error(field_name, f'{field_name} must be at least {min_length} characters')
            return False
        
        if max_length and len(value) > max_length:
            self.add_error(field_name, f'{field_name} must be no more than {max_length} characters')
            return False
        
        return True
    
    def is_valid(self) -> bool:
        """Check if validation passed"""
        return len(self.errors) == 0
    
    def get_errors(self) -> List[Dict[str, str]]:
        """Get all validation errors"""
        return self.errors
    
    def reset(self) -> None:
        """Reset validator state"""
        self.errors = []


# Enhanced Security and Validation Features

logger = logging.getLogger(__name__)

class BaseValidationSchema(Schema):
    """Base schema with common validation rules and error handling"""
    
    def handle_error(self, error, data, **kwargs):
        """Handle validation errors with detailed logging"""
        logger.warning(f"Validation error: {error.messages} for data: {str(data)[:100]}")
        raise MarshmallowValidationError(error.messages)
    
    @pre_load
    def strip_whitespace(self, data, **kwargs):
        """Strip whitespace from string fields"""
        if isinstance(data, dict):
            return {key: value.strip() if isinstance(value, str) else value 
                   for key, value in data.items()}
        return data

class UserRegistrationSchema(BaseValidationSchema):
    """Schema for user registration validation"""
    email = fields.Email(
        required=True,
        validate=validate.Length(max=120),
        error_messages={'invalid': 'Please enter a valid email address'}
    )
    password = fields.Str(
        required=True,
        validate=[
            validate.Length(min=8, max=128),
            validate.Regexp(
                r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)',
                error='Password must contain at least one lowercase letter, one uppercase letter, and one digit'
            )
        ]
    )
    first_name = fields.Str(
        required=True,
        validate=[
            validate.Length(min=1, max=64),
            validate.Regexp(r'^[a-zA-Z\s\-\'\.]+$', error='First name contains invalid characters')
        ]
    )
    last_name = fields.Str(
        required=True,
        validate=[
            validate.Length(min=1, max=64),
            validate.Regexp(r'^[a-zA-Z\s\-\'\.]+$', error='Last name contains invalid characters')
        ]
    )
    phone = fields.Str(
        validate=[
            validate.Length(max=20),
            validate.Regexp(r'^\+?[\d\s\-\(\)]+$', error='Phone number format is invalid')
        ],
        allow_none=True,
        missing=None
    )
    
    @post_load
    def sanitize_data(self, data, **kwargs):
        """Sanitize input data"""
        if 'first_name' in data:
            data['first_name'] = sanitize_text_input(data['first_name'])
        if 'last_name' in data:
            data['last_name'] = sanitize_text_input(data['last_name'])
        return data

class PropertyCreationSchema(BaseValidationSchema):
    """Schema for property creation validation"""
    name = fields.Str(
        required=True,
        validate=[
            validate.Length(min=1, max=128),
            validate.Regexp(r'^[a-zA-Z0-9\s\-\.\,\#]+$', error='Property name contains invalid characters')
        ]
    )
    address = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=256)
    )
    property_type = fields.Str(
        required=True,
        validate=validate.OneOf(['apartment', 'house', 'condo', 'townhouse', 'suite'])
    )
    bedrooms = fields.Int(
        validate=validate.Range(min=0, max=50),
        allow_none=True,
        missing=None
    )
    bathrooms = fields.Float(
        validate=validate.Range(min=0, max=50),
        allow_none=True,
        missing=None
    )
    description = fields.Str(
        validate=validate.Length(max=2000),
        allow_none=True,
        missing=None
    )
    
    @post_load
    def sanitize_data(self, data, **kwargs):
        """Sanitize input data"""
        for field in ['name', 'address', 'description']:
            if field in data and data[field]:
                data[field] = sanitize_text_input(data[field])
        return data

class TaskCreationSchema(BaseValidationSchema):
    """Schema for task creation validation"""
    title = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=128)
    )
    description = fields.Str(
        validate=validate.Length(max=2000),
        allow_none=True,
        missing=None
    )
    priority = fields.Str(
        validate=validate.OneOf(['low', 'normal', 'high', 'urgent']),
        missing='normal'
    )
    due_date = fields.DateTime(
        allow_none=True,
        missing=None,
        format='iso'
    )
    property_id = fields.Int(
        required=True,
        validate=validate.Range(min=1)
    )
    assignee_id = fields.Int(
        validate=validate.Range(min=1),
        allow_none=True,
        missing=None
    )
    
    @post_load
    def sanitize_data(self, data, **kwargs):
        """Sanitize input data"""
        for field in ['title', 'description']:
            if field in data and data[field]:
                data[field] = sanitize_text_input(data[field])
        return data

def validate_request(schema_class):
    """Decorator for request validation using Marshmallow schemas"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            schema = schema_class()
            
            try:
                # Get data from request
                if request.is_json:
                    data = request.get_json() or {}
                else:
                    data = request.form.to_dict()
                
                # Validate data
                validated_data = schema.load(data)
                request.validated_data = validated_data
                
            except MarshmallowValidationError as e:
                logger.warning(f"Validation failed for {request.endpoint}: {e.messages}")
                abort(400, description=f"Validation error: {e.messages}")
            except Exception as e:
                logger.error(f"Unexpected validation error: {e}")
                abort(400, description="Invalid request data")
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def sanitize_sql_input(value):
    """Sanitize input to prevent SQL injection"""
    if not isinstance(value, str):
        return value
    
    # Remove dangerous SQL characters and keywords
    dangerous_patterns = [
        r'[;\'"\\]',  # SQL injection characters
        r'--',        # SQL comments
        r'/\*.*?\*/', # SQL block comments
        r'\b(DROP|DELETE|INSERT|UPDATE|UNION|SELECT)\b'  # SQL keywords
    ]
    
    for pattern in dangerous_patterns:
        value = re.sub(pattern, '', value, flags=re.IGNORECASE)
    
    # Limit length
    if len(value) > 255:
        value = value[:255]
    
    return value.strip()

def sanitize_html_advanced(value):
    """Advanced HTML sanitization allowing safe tags"""
    if not isinstance(value, str):
        return value
    
    # Remove null bytes
    value = value.replace('\x00', '')
    
    # Define allowed tags and attributes
    allowed_tags = [
        'p', 'br', 'strong', 'em', 'b', 'i', 'u', 
        'ul', 'ol', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'blockquote', 'a'
    ]
    
    allowed_attributes = {
        'a': ['href', 'title'],
        '*': ['class']
    }
    
    # Clean with bleach
    value = bleach.clean(
        value,
        tags=allowed_tags,
        attributes=allowed_attributes,
        strip=True
    )
    
    return value

def validate_file_upload(file, allowed_extensions=None, max_size=None):
    """Validate file uploads with security checks"""
    if not file or not file.filename:
        raise ValidationError("No file provided")
    
    # Check file extension
    if allowed_extensions:
        file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
        if file_ext not in allowed_extensions:
            raise ValidationError(f"File type not allowed. Allowed types: {', '.join(allowed_extensions)}")
    
    # Check file size
    if max_size:
        file.seek(0, 2)  # Seek to end
        file_size = file.tell()
        file.seek(0)     # Reset to beginning
        
        if file_size > max_size:
            raise ValidationError(f"File too large. Maximum size: {max_size / 1024 / 1024:.1f}MB")
    
    # Check for dangerous file content
    dangerous_headers = [
        b'<script',
        b'<?php',
        b'<%',
        b'\x4d\x5a'  # PE executable header
    ]
    
    file_content = file.read(1024)  # Read first 1KB
    file.seek(0)  # Reset
    
    for header in dangerous_headers:
        if header in file_content.lower():
            raise ValidationError("File contains potentially dangerous content")
    
    return True

def validate_email_advanced(email):
    """Advanced email validation using email-validator"""
    try:
        # Validate and get normalized result
        validation = validate_email_lib(email)
        return validation.email
    except EmailNotValidError as e:
        raise ValidationError(f"Invalid email address: {str(e)}")

class SecurityValidator:
    """Advanced security validation utilities"""
    
    @staticmethod
    def validate_csrf_token(token, session_token):
        """Validate CSRF token"""
        if not token or not session_token:
            return False
        return token == session_token
    
    @staticmethod
    def validate_password_strength_advanced(password):
        """Advanced password strength validation"""
        errors = []
        
        if len(password) < 8:
            errors.append("Password must be at least 8 characters long")
        
        if not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")
        
        if not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")
        
        if not re.search(r'\d', password):
            errors.append("Password must contain at least one digit")
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("Password must contain at least one special character")
        
        # Check for common passwords
        common_passwords = [
            'password', '123456', 'password123', 'admin', 'qwerty',
            'letmein', 'welcome', 'monkey', '1234567890'
        ]
        
        if password.lower() in common_passwords:
            errors.append("Password is too common")
        
        if errors:
            raise ValidationError(errors)
        
        return True
    
    @staticmethod
    def validate_user_agent(user_agent):
        """Validate and categorize user agent"""
        if not user_agent:
            return False
        
        # Check for suspicious patterns
        suspicious_patterns = [
            r'bot', r'crawler', r'spider', r'scraper',
            r'curl', r'wget', r'python', r'requests'
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, user_agent, re.IGNORECASE):
                logger.warning(f"Suspicious user agent detected: {user_agent}")
                return False
        
        return True
    
    @staticmethod
    def validate_request_origin(origin, allowed_origins):
        """Validate request origin against allowed origins"""
        if not origin:
            return False
        
        return origin in allowed_origins

def rate_limit_key(user_id=None, ip_address=None):
    """Generate rate limiting key"""
    if user_id:
        return f"user_rate_limit_{user_id}"
    elif ip_address:
        return f"ip_rate_limit_{ip_address}"
    else:
        return "global_rate_limit"