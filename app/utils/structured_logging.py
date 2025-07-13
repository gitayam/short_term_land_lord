"""
Structured Logging System

This module provides comprehensive structured logging capabilities with JSON formatting,
request context, security event logging, and centralized log management.
"""

import json
import logging
import logging.handlers
import os
import traceback
import uuid
from datetime import datetime
from flask import request, g, current_app, has_request_context
from flask_login import current_user
from functools import wraps
import sys

class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""
    
    def format(self, record):
        """Format log record as JSON"""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'thread': record.thread,
            'process': record.process
        }
        
        # Add request context if available
        if has_request_context():
            try:
                log_entry.update({
                    'request_id': getattr(g, 'request_id', None),
                    'method': request.method,
                    'path': request.path,
                    'remote_addr': request.remote_addr,
                    'user_agent': request.headers.get('User-Agent', ''),
                    'referrer': request.headers.get('Referer', ''),
                    'content_type': request.headers.get('Content-Type', ''),
                    'content_length': request.headers.get('Content-Length', 0)
                })
                
                # Add query parameters (sanitized)
                if request.args:
                    log_entry['query_params'] = dict(request.args)
                
                # Add form data (sanitized - exclude passwords)
                if request.form:
                    form_data = dict(request.form)
                    # Remove sensitive fields
                    sensitive_fields = ['password', 'password_confirm', 'current_password', 'new_password']
                    for field in sensitive_fields:
                        if field in form_data:
                            form_data[field] = '[REDACTED]'
                    log_entry['form_data'] = form_data
                
            except Exception as e:
                log_entry['request_context_error'] = str(e)
        
        # Add user context if available
        try:
            if current_user and hasattr(current_user, 'is_authenticated') and current_user.is_authenticated:
                log_entry.update({
                    'user_id': getattr(current_user, 'id', None),
                    'user_email': getattr(current_user, 'email', None),
                    'user_role': getattr(current_user, 'role', None),
                    'is_admin': getattr(current_user, 'is_admin', False)
                })
        except Exception as e:
            log_entry['user_context_error'] = str(e)
        
        # Add custom fields from record
        if hasattr(record, 'custom_fields'):
            log_entry.update(record.custom_fields)
        
        # Add exception information if present
        if record.exc_info:
            log_entry['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }
        
        # Add extra fields from record
        extra_fields = {}
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                          'filename', 'module', 'exc_info', 'exc_text', 'stack_info',
                          'lineno', 'funcName', 'created', 'msecs', 'relativeCreated',
                          'thread', 'threadName', 'processName', 'process', 'getMessage',
                          'custom_fields']:
                extra_fields[key] = value
        
        if extra_fields:
            log_entry['extra'] = extra_fields
        
        return json.dumps(log_entry, ensure_ascii=False, default=str)

class StructuredLogger:
    """Main structured logging manager"""
    
    def __init__(self, app=None):
        self.app = app
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize structured logging with Flask app"""
        self.app = app
        self.setup_logging()
        self.setup_request_logging()
        
        # Store logger instance on app for easy access
        app.structured_logger = self
        
        # Add request ID to all requests
        @app.before_request
        def before_request():
            g.request_id = self.generate_request_id()
            g.request_start_time = datetime.utcnow()
        
        @app.after_request
        def after_request(response):
            if hasattr(g, 'request_start_time'):
                duration = (datetime.utcnow() - g.request_start_time).total_seconds()
                
                # Log request completion
                self.log_request_completion(
                    status_code=response.status_code,
                    duration=duration,
                    response_size=len(response.get_data()) if response.get_data() else 0
                )
            
            return response
        
        logging.info("Structured logging initialized")
    
    def setup_logging(self):
        """Setup logging configuration"""
        # Remove default handlers
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # Create formatters
        json_formatter = JSONFormatter()
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        if self.app.config.get('LOG_FORMAT') == 'json':
            console_handler.setFormatter(json_formatter)
        else:
            console_handler.setFormatter(console_formatter)
        
        # File handler for structured logs
        log_file = self.app.config.get('LOG_FILE')
        if log_file:
            try:
                os.makedirs(os.path.dirname(log_file), exist_ok=True)
                file_handler = logging.handlers.RotatingFileHandler(
                    log_file,
                    maxBytes=10 * 1024 * 1024,  # 10MB
                    backupCount=5
                )
                file_handler.setFormatter(json_formatter)
                
                # Add file handler to root logger
                root_logger.addHandler(file_handler)
            except Exception as e:
                logging.error(f"Failed to create file handler: {e}")
        
        # Add console handler to root logger
        root_logger.addHandler(console_handler)
        
        # Set log level
        log_level = self.app.config.get('LOG_LEVEL', 'INFO')
        root_logger.setLevel(getattr(logging, log_level.upper()))
        
        # Configure specific loggers
        self.setup_logger_levels()
    
    def setup_logger_levels(self):
        """Configure specific logger levels"""
        # Reduce noise from third-party libraries
        logging.getLogger('werkzeug').setLevel(logging.WARNING)
        logging.getLogger('urllib3').setLevel(logging.WARNING)
        logging.getLogger('requests').setLevel(logging.WARNING)
        
        # Application loggers
        logging.getLogger('app').setLevel(logging.INFO)
        logging.getLogger('app.security').setLevel(logging.WARNING)
        logging.getLogger('app.business').setLevel(logging.INFO)
        logging.getLogger('app.performance').setLevel(logging.WARNING)
    
    def setup_request_logging(self):
        """Setup request-specific logging"""
        @self.app.before_request
        def log_request_start():
            self.log_request_start()
        
        @self.app.teardown_request
        def log_request_end(exception=None):
            if exception:
                self.log_request_error(exception)
    
    def generate_request_id(self):
        """Generate unique request ID"""
        return str(uuid.uuid4())
    
    def log_request_start(self):
        """Log request start"""
        logger = logging.getLogger('app.request')
        logger.info("Request started", extra={
            'custom_fields': {
                'event_type': 'request_start',
                'endpoint': request.endpoint,
                'view_args': request.view_args
            }
        })
    
    def log_request_completion(self, status_code, duration, response_size):
        """Log request completion"""
        logger = logging.getLogger('app.request')
        log_level = logging.INFO
        
        # Use different log levels based on status code
        if status_code >= 500:
            log_level = logging.ERROR
        elif status_code >= 400:
            log_level = logging.WARNING
        elif duration > 1.0:  # Slow requests
            log_level = logging.WARNING
        
        logger.log(log_level, f"Request completed - {status_code}", extra={
            'custom_fields': {
                'event_type': 'request_complete',
                'status_code': status_code,
                'duration_seconds': duration,
                'response_size_bytes': response_size,
                'endpoint': request.endpoint
            }
        })
    
    def log_request_error(self, exception):
        """Log request error"""
        logger = logging.getLogger('app.request')
        logger.error(f"Request error: {exception}", exc_info=True, extra={
            'custom_fields': {
                'event_type': 'request_error',
                'exception_type': type(exception).__name__,
                'endpoint': request.endpoint
            }
        })
    
    def log_business_event(self, event_type, details, user_id=None):
        """Log business events"""
        logger = logging.getLogger('app.business')
        logger.info(f"Business event: {event_type}", extra={
            'custom_fields': {
                'event_type': event_type,
                'details': details,
                'business_user_id': user_id or (current_user.id if current_user.is_authenticated else None)
            }
        })
    
    def log_security_event(self, event_type, details, severity='medium', user_id=None, ip_address=None):
        """Log security events"""
        logger = logging.getLogger('app.security')
        
        # Determine log level based on severity
        log_level = logging.WARNING
        if severity == 'high':
            log_level = logging.ERROR
        elif severity == 'low':
            log_level = logging.INFO
        
        logger.log(log_level, f"Security event: {event_type}", extra={
            'custom_fields': {
                'event_type': event_type,
                'details': details,
                'severity': severity,
                'security_user_id': user_id or (current_user.id if current_user.is_authenticated else None),
                'security_ip_address': ip_address or (request.remote_addr if has_request_context() else None)
            }
        })
    
    def log_performance_event(self, operation, duration, details=None):
        """Log performance events"""
        logger = logging.getLogger('app.performance')
        
        # Log level based on duration
        log_level = logging.INFO
        if duration > 5.0:
            log_level = logging.ERROR
        elif duration > 2.0:
            log_level = logging.WARNING
        
        logger.log(log_level, f"Performance: {operation} took {duration:.2f}s", extra={
            'custom_fields': {
                'event_type': 'performance',
                'operation': operation,
                'duration_seconds': duration,
                'details': details or {}
            }
        })
    
    def log_database_event(self, operation, table, duration, query=None):
        """Log database events"""
        logger = logging.getLogger('app.database')
        
        log_level = logging.DEBUG
        if duration > 1.0:
            log_level = logging.WARNING
        elif duration > 0.5:
            log_level = logging.INFO
        
        logger.log(log_level, f"Database {operation} on {table}", extra={
            'custom_fields': {
                'event_type': 'database',
                'operation': operation,
                'table': table,
                'duration_seconds': duration,
                'query': query[:200] if query else None  # Truncate long queries
            }
        })

def log_with_context(logger_name='app'):
    """Decorator to add logging context to functions"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            logger = logging.getLogger(logger_name)
            func_name = f.__name__
            
            start_time = datetime.utcnow()
            logger.debug(f"Function {func_name} started", extra={
                'custom_fields': {
                    'event_type': 'function_start',
                    'function_name': func_name,
                    'args_count': len(args),
                    'kwargs_count': len(kwargs)
                }
            })
            
            try:
                result = f(*args, **kwargs)
                duration = (datetime.utcnow() - start_time).total_seconds()
                
                logger.debug(f"Function {func_name} completed", extra={
                    'custom_fields': {
                        'event_type': 'function_complete',
                        'function_name': func_name,
                        'duration_seconds': duration
                    }
                })
                
                return result
            except Exception as e:
                duration = (datetime.utcnow() - start_time).total_seconds()
                
                logger.error(f"Function {func_name} failed: {e}", exc_info=True, extra={
                    'custom_fields': {
                        'event_type': 'function_error',
                        'function_name': func_name,
                        'duration_seconds': duration,
                        'exception_type': type(e).__name__
                    }
                })
                raise
        
        return decorated_function
    return decorator

class AuditLogger:
    """Specialized logger for audit events"""
    
    def __init__(self):
        self.logger = logging.getLogger('app.audit')
    
    def log_user_action(self, action, resource_type, resource_id, details=None):
        """Log user actions for audit trail"""
        self.logger.info(f"User action: {action}", extra={
            'custom_fields': {
                'event_type': 'user_action',
                'action': action,
                'resource_type': resource_type,
                'resource_id': resource_id,
                'details': details or {},
                'audit_user_id': current_user.id if current_user.is_authenticated else None,
                'audit_timestamp': datetime.utcnow().isoformat()
            }
        })
    
    def log_admin_action(self, action, target_user_id, details=None):
        """Log administrative actions"""
        self.logger.warning(f"Admin action: {action}", extra={
            'custom_fields': {
                'event_type': 'admin_action',
                'action': action,
                'target_user_id': target_user_id,
                'details': details or {},
                'admin_user_id': current_user.id if current_user.is_authenticated else None,
                'audit_timestamp': datetime.utcnow().isoformat()
            }
        })
    
    def log_data_change(self, table, record_id, old_values, new_values, operation):
        """Log data changes for audit trail"""
        self.logger.info(f"Data change: {operation} on {table}", extra={
            'custom_fields': {
                'event_type': 'data_change',
                'table': table,
                'record_id': record_id,
                'operation': operation,
                'old_values': old_values,
                'new_values': new_values,
                'changed_by': current_user.id if current_user.is_authenticated else None,
                'audit_timestamp': datetime.utcnow().isoformat()
            }
        })

# Global instances
audit_logger = AuditLogger()

def init_structured_logging(app):
    """Initialize structured logging for the Flask app"""
    structured_logger = StructuredLogger(app)
    return structured_logger