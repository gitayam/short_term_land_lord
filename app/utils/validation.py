"""
Validation utilities for input sanitization and security
"""
import re
import bleach
from typing import Optional, Union, List, Dict, Any
from flask import current_app
from werkzeug.utils import secure_filename
import phonenumbers
from phonenumbers import NumberParseException


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