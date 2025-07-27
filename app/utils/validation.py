"""
Comprehensive input validation framework for production security
"""
import re
from marshmallow import Schema, fields, validate, ValidationError, pre_load, post_load
from flask import request, abort, current_app
from functools import wraps
import bleach
from datetime import datetime, date


# Custom validation functions
def validate_phone_number(value):
    """Validate phone number format"""
    phone_pattern = r'^\+?1?\d{9,15}$'
    if not re.match(phone_pattern, value):
        raise ValidationError('Invalid phone number format')


def validate_address(value):
    """Validate address format"""
    if len(value.strip()) < 5:
        raise ValidationError('Address must be at least 5 characters long')
    
    # Check for suspicious patterns
    suspicious_patterns = ['<script', 'javascript:', 'data:', 'vbscript:']
    value_lower = value.lower()
    for pattern in suspicious_patterns:
        if pattern in value_lower:
            raise ValidationError('Invalid characters in address')


def validate_property_type(value):
    """Validate property type"""
    valid_types = ['apartment', 'house', 'condo', 'townhouse', 'studio', 'suite']
    if value.lower() not in valid_types:
        raise ValidationError(f'Property type must be one of: {", ".join(valid_types)}')


def validate_user_role(value):
    """Validate user role"""
    valid_roles = ['admin', 'property_owner', 'staff', 'cleaner', 'maintenance', 'guest']
    if value.lower() not in valid_roles:
        raise ValidationError(f'User role must be one of: {", ".join(valid_roles)}')


def sanitize_html_input(value):
    """Sanitize HTML input to prevent XSS"""
    if isinstance(value, str):
        # Allow only safe HTML tags
        allowed_tags = ['p', 'br', 'strong', 'em', 'ul', 'ol', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']
        return bleach.clean(value, tags=allowed_tags, strip=True)
    return value


def sanitize_sql_input(value):
    """Sanitize input to prevent SQL injection"""
    if isinstance(value, str):
        # Remove dangerous characters
        value = re.sub(r'[;\'"\\]', '', value)
        # Limit length
        value = value[:1000]
    return value


# Base validation schema
class BaseValidationSchema(Schema):
    """Base schema with common validation rules and sanitization"""
    
    class Meta:
        # Don't include unknown fields
        unknown = 'EXCLUDE'
    
    @pre_load
    def sanitize_inputs(self, data, **kwargs):
        """Sanitize all string inputs before validation"""
        if isinstance(data, dict):
            sanitized_data = {}
            for key, value in data.items():
                if isinstance(value, str):
                    # Strip whitespace
                    value = value.strip()
                    # Sanitize HTML
                    value = sanitize_html_input(value)
                    # Sanitize SQL
                    value = sanitize_sql_input(value)
                sanitized_data[key] = value
            return sanitized_data
        return data
    
    def handle_error(self, error, data, **kwargs):
        """Custom error handling"""
        current_app.logger.warning(f"Validation error: {error.messages}")
        raise ValidationError(error.messages)


# User validation schemas
class UserRegistrationSchema(BaseValidationSchema):
    """Validation schema for user registration"""
    email = fields.Email(required=True, validate=validate.Length(max=120))
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
    first_name = fields.Str(required=True, validate=validate.Length(min=1, max=64))
    last_name = fields.Str(required=True, validate=validate.Length(min=1, max=64))
    phone = fields.Str(validate=validate_phone_number, allow_none=True)
    role = fields.Str(validate=validate_user_role, load_default='guest')


class UserUpdateSchema(BaseValidationSchema):
    """Validation schema for user updates"""
    email = fields.Email(validate=validate.Length(max=120))
    first_name = fields.Str(validate=validate.Length(min=1, max=64))
    last_name = fields.Str(validate=validate.Length(min=1, max=64))
    phone = fields.Str(validate=validate_phone_number, allow_none=True)
    timezone = fields.Str(validate=validate.Length(max=50))
    language = fields.Str(validate=validate.Length(max=10))
    theme_preference = fields.Str(validate=validate.OneOf(['light', 'dark']))


class UserLoginSchema(BaseValidationSchema):
    """Validation schema for user login"""
    email = fields.Email(required=True, validate=validate.Length(max=120))
    password = fields.Str(required=True, validate=validate.Length(min=1, max=128))
    remember_me = fields.Bool(load_default=False)


# Property validation schemas
class PropertyCreationSchema(BaseValidationSchema):
    """Validation schema for property creation"""
    name = fields.Str(required=True, validate=validate.Length(min=1, max=128))
    address = fields.Str(required=True, validate=[validate.Length(min=5, max=256), validate_address])
    description = fields.Str(validate=validate.Length(max=2000), allow_none=True)
    property_type = fields.Str(required=True, validate=validate_property_type)
    
    # Address components
    street_address = fields.Str(validate=validate.Length(max=128), allow_none=True)
    city = fields.Str(validate=validate.Length(max=64), allow_none=True)
    state = fields.Str(validate=validate.Length(max=64), allow_none=True)
    zip_code = fields.Str(validate=validate.Length(max=16), allow_none=True)
    country = fields.Str(validate=validate.Length(max=64), allow_none=True)
    
    # Property details
    bedrooms = fields.Int(validate=validate.Range(min=0, max=20), allow_none=True)
    bathrooms = fields.Float(validate=validate.Range(min=0, max=20), allow_none=True)
    square_feet = fields.Int(validate=validate.Range(min=1, max=50000), allow_none=True)
    year_built = fields.Int(validate=validate.Range(min=1800, max=datetime.now().year), allow_none=True)


class PropertyUpdateSchema(PropertyCreationSchema):
    """Validation schema for property updates - inherits from creation but nothing required"""
    name = fields.Str(validate=validate.Length(min=1, max=128))
    address = fields.Str(validate=[validate.Length(min=5, max=256), validate_address])
    property_type = fields.Str(validate=validate_property_type)


# Task validation schemas
class TaskCreationSchema(BaseValidationSchema):
    """Validation schema for task creation"""
    title = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    description = fields.Str(validate=validate.Length(max=2000), allow_none=True)
    priority = fields.Str(validate=validate.OneOf(['low', 'medium', 'high', 'urgent']), load_default='medium')
    due_date = fields.DateTime(allow_none=True)
    property_id = fields.Int(required=True, validate=validate.Range(min=1))
    assign_to_next_cleaner = fields.Bool(load_default=False)
    
    # Recurring task fields
    is_recurring = fields.Bool(load_default=False)
    recurrence_pattern = fields.Str(
        validate=validate.OneOf(['daily', 'weekly', 'monthly', 'yearly']),
        allow_none=True
    )
    recurrence_interval = fields.Int(validate=validate.Range(min=1, max=365), load_default=1)
    recurrence_end_date = fields.DateTime(allow_none=True)


class TaskUpdateSchema(TaskCreationSchema):
    """Validation schema for task updates"""
    title = fields.Str(validate=validate.Length(min=1, max=100))
    property_id = fields.Int(validate=validate.Range(min=1))
    status = fields.Str(validate=validate.OneOf(['pending', 'in_progress', 'completed', 'cancelled']))


# Message validation schemas
class MessageCreationSchema(BaseValidationSchema):
    """Validation schema for message creation"""
    recipient_id = fields.Int(required=True, validate=validate.Range(min=1))
    subject = fields.Str(validate=validate.Length(min=1, max=200), allow_none=True)
    content = fields.Str(required=True, validate=validate.Length(min=1, max=5000))
    message_type = fields.Str(validate=validate.OneOf(['email', 'sms', 'system']), load_default='system')


# File upload validation schemas
class FileUploadSchema(BaseValidationSchema):
    """Validation schema for file uploads"""
    file_type = fields.Str(required=True, validate=validate.OneOf(['photo', 'video', 'document']))
    description = fields.Str(validate=validate.Length(max=500), allow_none=True)
    
    @post_load
    def validate_file_size(self, data, **kwargs):
        """Validate file size limits"""
        max_size = current_app.config.get('MAX_CONTENT_LENGTH', 50 * 1024 * 1024)
        if request.content_length and request.content_length > max_size:
            raise ValidationError(f'File size exceeds maximum limit of {max_size / (1024*1024):.1f}MB')
        return data


# Search and filter validation schemas
class SearchSchema(BaseValidationSchema):
    """Validation schema for search queries"""
    query = fields.Str(validate=validate.Length(min=1, max=200))
    page = fields.Int(validate=validate.Range(min=1, max=1000), load_default=1)
    per_page = fields.Int(validate=validate.Range(min=1, max=100), load_default=20)
    sort_by = fields.Str(validate=validate.Length(max=50), allow_none=True)
    sort_order = fields.Str(validate=validate.OneOf(['asc', 'desc']), load_default='asc')


class PropertyFilterSchema(BaseValidationSchema):
    """Validation schema for property filtering"""
    property_type = fields.Str(validate=validate_property_type, allow_none=True)
    min_bedrooms = fields.Int(validate=validate.Range(min=0, max=20), allow_none=True)
    max_bedrooms = fields.Int(validate=validate.Range(min=0, max=20), allow_none=True)
    city = fields.Str(validate=validate.Length(max=64), allow_none=True)
    state = fields.Str(validate=validate.Length(max=64), allow_none=True)


# Validation decorators
def validate_request(schema_class, location='json'):
    """Decorator for request validation"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            schema = schema_class()
            
            try:
                # Get data based on location
                if location == 'json':
                    data = request.get_json() or {}
                elif location == 'form':
                    data = request.form.to_dict()
                elif location == 'args':
                    data = request.args.to_dict()
                else:
                    data = {}
                
                # Validate data
                validated_data = schema.load(data)
                
                # Store validated data in request context
                request.validated_data = validated_data
                
            except ValidationError as e:
                current_app.logger.warning(f"Validation failed for {request.endpoint}: {e.messages}")
                abort(400, description=f"Validation failed: {e.messages}")
            except Exception as e:
                current_app.logger.error(f"Validation error: {e}")
                abort(400, description="Invalid request data")
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def validate_query_params(schema_class):
    """Decorator for query parameter validation"""
    return validate_request(schema_class, location='args')


def validate_form_data(schema_class):
    """Decorator for form data validation"""
    return validate_request(schema_class, location='form')


def validate_json_data(schema_class):
    """Decorator for JSON data validation"""
    return validate_request(schema_class, location='json')


# Security validation utilities
class SecurityValidator:
    """Security-focused validation utilities"""
    
    @staticmethod
    def validate_csrf_token():
        """Validate CSRF token for non-GET requests"""
        if request.method != 'GET' and not request.is_json:
            from flask_wtf.csrf import validate_csrf
            try:
                validate_csrf(request.form.get('csrf_token'))
            except ValidationError:
                current_app.logger.warning(f"CSRF validation failed for {request.endpoint}")
                abort(400, description="CSRF token validation failed")
    
    @staticmethod
    def validate_file_upload(file):
        """Validate uploaded file for security"""
        if not file or not file.filename:
            raise ValidationError("No file provided")
        
        # Check file extension
        allowed_extensions = current_app.config.get('ALLOWED_PHOTO_EXTENSIONS', set()) | \
                           current_app.config.get('ALLOWED_VIDEO_EXTENSIONS', set())
        
        if allowed_extensions:
            file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
            if file_ext not in allowed_extensions:
                raise ValidationError(f"File type .{file_ext} not allowed")
        
        # Check file size
        max_size = current_app.config.get('MAX_CONTENT_LENGTH', 50 * 1024 * 1024)
        if hasattr(file, 'content_length') and file.content_length > max_size:
            raise ValidationError(f"File size exceeds {max_size / (1024*1024):.1f}MB limit")
        
        return True
    
    @staticmethod
    def validate_api_key(api_key):
        """Validate API key format and structure"""
        if not api_key:
            raise ValidationError("API key required")
        
        # Basic format validation
        if not re.match(r'^[A-Za-z0-9_-]{32,}$', api_key):
            raise ValidationError("Invalid API key format")
        
        return True


# Error response formatter
def format_validation_errors(errors):
    """Format validation errors for API responses"""
    formatted_errors = []
    
    def flatten_errors(error_dict, parent_key=''):
        for key, value in error_dict.items():
            full_key = f"{parent_key}.{key}" if parent_key else key
            
            if isinstance(value, dict):
                flatten_errors(value, full_key)
            elif isinstance(value, list):
                for error in value:
                    formatted_errors.append({
                        'field': full_key,
                        'message': error,
                        'code': 'validation_error'
                    })
            else:
                formatted_errors.append({
                    'field': full_key,
                    'message': value,
                    'code': 'validation_error'
                })
    
    if isinstance(errors, dict):
        flatten_errors(errors)
    else:
        formatted_errors.append({
            'field': 'general',
            'message': str(errors),
            'code': 'validation_error'
        })
    
    return {
        'success': False,
        'errors': formatted_errors,
        'error_count': len(formatted_errors)
    }