"""
Enhanced error handling utilities
"""
import traceback
import sys
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from functools import wraps
from flask import current_app, request, jsonify, render_template
from werkzeug.exceptions import HTTPException
from flask_wtf.csrf import CSRFError
import logging


class AppError(Exception):
    """Base application error class"""
    
    def __init__(self, message: str, code: int = 500, details: Optional[Dict] = None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}
        self.timestamp = datetime.utcnow()


class ValidationError(AppError):
    """Validation error"""
    
    def __init__(self, message: str, field: Optional[str] = None, details: Optional[Dict] = None):
        super().__init__(message, 400, details)
        self.field = field


class BusinessLogicError(AppError):
    """Business logic error"""
    
    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__(message, 422, details)


class NotFoundError(AppError):
    """Resource not found error"""
    
    def __init__(self, resource: str, identifier: Any = None):
        message = f"{resource} not found"
        if identifier:
            message += f" (ID: {identifier})"
        super().__init__(message, 404)
        self.resource = resource
        self.identifier = identifier


class PermissionError(AppError):
    """Permission denied error"""
    
    def __init__(self, message: str = "Permission denied", details: Optional[Dict] = None):
        super().__init__(message, 403, details)


class RateLimitError(AppError):
    """Rate limit exceeded error"""
    
    def __init__(self, message: str = "Rate limit exceeded", retry_after: Optional[int] = None):
        super().__init__(message, 429)
        self.retry_after = retry_after


def handle_errors(f):
    """Decorator for comprehensive error handling"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        
        except ValidationError as e:
            return handle_validation_error(e)
        
        except BusinessLogicError as e:
            return handle_business_logic_error(e)
        
        except NotFoundError as e:
            return handle_not_found_error(e)
        
        except PermissionError as e:
            return handle_permission_error(e)
        
        except RateLimitError as e:
            return handle_rate_limit_error(e)
        
        except AppError as e:
            return handle_app_error(e)
        
        except HTTPException as e:
            return handle_http_error(e)
        
        except Exception as e:
            return handle_unexpected_error(e)
    
    return decorated_function


def handle_validation_error(error: ValidationError) -> Tuple[Dict, int]:
    """Handle validation errors"""
    log_error("ValidationError", error)
    
    response = {
        'error': 'validation_error',
        'message': error.message,
        'field': error.field,
        'details': error.details
    }
    
    if is_api_request():
        return jsonify(response), error.code
    else:
        return render_error_page(error.code, error.message, error.details)


def handle_business_logic_error(error: BusinessLogicError) -> Tuple[Dict, int]:
    """Handle business logic errors"""
    log_error("BusinessLogicError", error)
    
    response = {
        'error': 'business_logic_error',
        'message': error.message,
        'details': error.details
    }
    
    if is_api_request():
        return jsonify(response), error.code
    else:
        return render_error_page(error.code, error.message, error.details)


def handle_not_found_error(error: NotFoundError) -> Tuple[Dict, int]:
    """Handle not found errors"""
    log_error("NotFoundError", error)
    
    response = {
        'error': 'not_found',
        'message': error.message,
        'resource': error.resource,
        'identifier': error.identifier
    }
    
    if is_api_request():
        return jsonify(response), error.code
    else:
        return render_error_page(404, "Resource not found", {"resource": error.resource})


def handle_permission_error(error: PermissionError) -> Tuple[Dict, int]:
    """Handle permission errors"""
    log_error("PermissionError", error)
    
    response = {
        'error': 'permission_denied',
        'message': error.message,
        'details': error.details
    }
    
    if is_api_request():
        return jsonify(response), error.code
    else:
        return render_error_page(403, "Access denied", error.details)


def handle_rate_limit_error(error: RateLimitError) -> Tuple[Dict, int]:
    """Handle rate limit errors"""
    log_error("RateLimitError", error)
    
    response = {
        'error': 'rate_limit_exceeded',
        'message': error.message,
        'retry_after': error.retry_after
    }
    
    if is_api_request():
        resp = jsonify(response)
        if error.retry_after:
            resp.headers['Retry-After'] = str(error.retry_after)
        return resp, error.code
    else:
        return render_error_page(429, "Too many requests", {"retry_after": error.retry_after})


def handle_app_error(error: AppError) -> Tuple[Dict, int]:
    """Handle generic app errors"""
    log_error("AppError", error)
    
    response = {
        'error': 'application_error',
        'message': error.message,
        'details': error.details
    }
    
    if is_api_request():
        return jsonify(response), error.code
    else:
        return render_error_page(error.code, error.message, error.details)


def handle_http_error(error: HTTPException) -> Tuple[Dict, int]:
    """Handle HTTP errors"""
    log_error("HTTPException", error)
    
    response = {
        'error': 'http_error',
        'message': error.description or "HTTP error occurred",
        'code': error.code
    }
    
    if is_api_request():
        return jsonify(response), error.code
    else:
        return render_error_page(error.code, error.description or "An error occurred")


def handle_unexpected_error(error: Exception) -> Tuple[Dict, int]:
    """Handle unexpected errors"""
    log_error("UnexpectedError", error, include_traceback=True)
    
    # Don't expose internal error details in production
    if current_app.debug:
        message = str(error)
        details = {
            'type': type(error).__name__,
            'traceback': traceback.format_exc()
        }
    else:
        message = "An unexpected error occurred"
        details = {}
    
    response = {
        'error': 'internal_error',
        'message': message,
        'details': details
    }
    
    if is_api_request():
        return jsonify(response), 500
    else:
        return render_error_page(500, message, details)


def log_error(error_type: str, error: Exception, include_traceback: bool = False):
    """Log error with context"""
    log_data = {
        'error_type': error_type,
        'error_message': str(error),
        'timestamp': datetime.utcnow().isoformat(),
        'request_url': request.url if request else None,
        'request_method': request.method if request else None,
        'remote_addr': request.remote_addr if request else None,
        'user_agent': request.headers.get('User-Agent') if request else None,
    }
    
    # Add user context if available
    try:
        from flask_login import current_user
        if current_user.is_authenticated:
            log_data['user_id'] = current_user.id
            log_data['user_email'] = current_user.email
    except:
        pass
    
    # Add traceback for unexpected errors
    if include_traceback:
        log_data['traceback'] = traceback.format_exc()
    
    # Add error-specific data
    if hasattr(error, 'details'):
        log_data['error_details'] = error.details
    
    current_app.logger.error(f"{error_type}: {str(error)}", extra=log_data)


def is_api_request() -> bool:
    """Check if request is for API endpoint"""
    return (
        request.is_json or 
        'application/json' in request.headers.get('Accept', '') or
        request.path.startswith('/api/')
    )


def render_error_page(code: int, message: str, details: Optional[Dict] = None):
    """Render error page for web requests"""
    try:
        # Try to render custom error template
        template_name = f"errors/{code}.html"
        return render_template(
            template_name,
            error_code=code,
            error_message=message,
            error_details=details
        ), code
    except:
        # Fallback to generic error template
        try:
            return render_template(
                "errors/generic.html",
                error_code=code,
                error_message=message,
                error_details=details
            ), code
        except:
            # Ultimate fallback - plain HTML
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Error {code}</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 40px; }}
                    .error {{ background: #f8f8f8; padding: 20px; border-radius: 5px; }}
                    .error-code {{ color: #d32f2f; font-size: 24px; font-weight: bold; }}
                    .error-message {{ margin: 10px 0; }}
                </style>
            </head>
            <body>
                <div class="error">
                    <div class="error-code">Error {code}</div>
                    <div class="error-message">{message}</div>
                </div>
            </body>
            </html>
            """
            return html, code


def safe_execute(func, *args, default=None, log_errors=True, **kwargs):
    """
    Safely execute a function with error handling
    
    Args:
        func: Function to execute
        args: Function arguments
        default: Default value to return on error
        log_errors: Whether to log errors
        kwargs: Function keyword arguments
    
    Returns:
        Function result or default value on error
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        if log_errors:
            current_app.logger.error(f"Error in safe_execute: {str(e)}")
        return default


class ErrorAggregator:
    """Collect and manage multiple errors"""
    
    def __init__(self):
        self.errors = []
    
    def add_error(self, error_type: str, message: str, field: Optional[str] = None, 
                  details: Optional[Dict] = None):
        """Add an error to the collection"""
        self.errors.append({
            'type': error_type,
            'message': message,
            'field': field,
            'details': details or {},
            'timestamp': datetime.utcnow().isoformat()
        })
    
    def has_errors(self) -> bool:
        """Check if there are any errors"""
        return len(self.errors) > 0
    
    def get_errors(self) -> list:
        """Get all errors"""
        return self.errors
    
    def get_errors_by_field(self, field: str) -> list:
        """Get errors for a specific field"""
        return [error for error in self.errors if error.get('field') == field]
    
    def clear(self):
        """Clear all errors"""
        self.errors = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format"""
        return {
            'has_errors': self.has_errors(),
            'error_count': len(self.errors),
            'errors': self.errors
        }


def create_error_response(message: str, code: int = 400, details: Optional[Dict] = None, 
                         field: Optional[str] = None) -> Tuple[Dict, int]:
    """
    Create standardized error response
    
    Args:
        message: Error message
        code: HTTP status code
        details: Additional error details
        field: Field name for validation errors
    
    Returns:
        Tuple of (response_dict, status_code)
    """
    response = {
        'success': False,
        'error': {
            'message': message,
            'code': code,
            'timestamp': datetime.utcnow().isoformat()
        }
    }
    
    if details:
        response['error']['details'] = details
    
    if field:
        response['error']['field'] = field
    
    return response, code


def create_success_response(data: Any = None, message: str = "Success") -> Dict[str, Any]:
    """
    Create standardized success response
    
    Args:
        data: Response data
        message: Success message
    
    Returns:
        Response dictionary
    """
    response = {
        'success': True,
        'message': message,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    if data is not None:
        response['data'] = data
    
    return response