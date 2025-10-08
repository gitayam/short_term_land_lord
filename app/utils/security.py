"""
Security utilities for the application
"""
import secrets
import hashlib
import hmac
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from functools import wraps
from flask import request, current_app, session, abort, g, flash, redirect, url_for
from werkzeug.exceptions import TooManyRequests


class RateLimiter:
    """
    Simple in-memory rate limiter
    In production, consider using Redis for distributed rate limiting
    """
    
    def __init__(self):
        self._requests = {}
        self._last_cleanup = time.time()
    
    def _cleanup_old_entries(self):
        """Clean up old entries to prevent memory leaks"""
        current_time = time.time()
        if current_time - self._last_cleanup > 3600:  # Cleanup every hour
            cutoff = current_time - 3600  # Remove entries older than 1 hour
            self._requests = {
                key: timestamps for key, timestamps in self._requests.items()
                if any(ts > cutoff for ts in timestamps)
            }
            self._last_cleanup = current_time
    
    def is_allowed(self, key: str, limit: int, window: int) -> bool:
        """
        Check if request is allowed within rate limit
        
        Args:
            key: Unique identifier (IP, user ID, etc.)
            limit: Maximum number of requests
            window: Time window in seconds
        
        Returns:
            True if allowed, False if rate limited
        """
        current_time = time.time()
        cutoff = current_time - window
        
        # Clean up old entries periodically
        self._cleanup_old_entries()
        
        if key not in self._requests:
            self._requests[key] = []
        
        # Remove old timestamps
        self._requests[key] = [ts for ts in self._requests[key] if ts > cutoff]
        
        # Check if under limit
        if len(self._requests[key]) < limit:
            self._requests[key].append(current_time)
            return True
        
        return False
    
    def reset(self, key: str):
        """Reset rate limit for a key"""
        if key in self._requests:
            del self._requests[key]


# Global rate limiter instance
rate_limiter = RateLimiter()


def rate_limit(limit: int = 100, window: int = 3600, per: str = 'ip', 
               message: str = "Rate limit exceeded"):
    """
    Decorator for rate limiting endpoints
    
    Args:
        limit: Maximum number of requests
        window: Time window in seconds
        per: Rate limiting key ('ip', 'user', or custom function)
        message: Error message when rate limited
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Determine rate limiting key
            if per == 'ip':
                key = f"ip:{request.remote_addr}"
            elif per == 'user':
                from flask_login import current_user
                if current_user.is_authenticated:
                    key = f"user:{current_user.id}"
                else:
                    key = f"ip:{request.remote_addr}"
            elif callable(per):
                key = per()
            else:
                key = f"ip:{request.remote_addr}"
            
            if not rate_limiter.is_allowed(key, limit, window):
                current_app.logger.warning(f"Rate limit exceeded for {key}")
                raise TooManyRequests(message)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def generate_csrf_token() -> str:
    """Generate a CSRF token"""
    if 'csrf_token' not in session:
        session['csrf_token'] = secrets.token_hex(32)
    return session['csrf_token']


def validate_csrf_token(token: str) -> bool:
    """Validate CSRF token"""
    session_token = session.get('csrf_token')
    if not session_token or not token:
        return False
    return hmac.compare_digest(session_token, token)


def require_csrf(f):
    """Decorator to require CSRF token validation"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            token = request.form.get('csrf_token') or request.headers.get('X-CSRF-Token')
            if not validate_csrf_token(token):
                current_app.logger.warning(f"CSRF validation failed for {request.endpoint}")
                abort(403)
        return f(*args, **kwargs)
    return decorated_function


def generate_secure_token(length: int = 32) -> str:
    """Generate a cryptographically secure token"""
    return secrets.token_urlsafe(length)


def hash_with_salt(data: str, salt: Optional[str] = None) -> Tuple[str, str]:
    """
    Hash data with salt
    
    Args:
        data: Data to hash
        salt: Salt to use (generated if not provided)
    
    Returns:
        Tuple of (hash, salt)
    """
    if salt is None:
        salt = secrets.token_hex(16)
    
    combined = f"{data}{salt}".encode('utf-8')
    hash_value = hashlib.sha256(combined).hexdigest()
    
    return hash_value, salt


def verify_hash(data: str, hash_value: str, salt: str) -> bool:
    """Verify hashed data"""
    computed_hash, _ = hash_with_salt(data, salt)
    return hmac.compare_digest(computed_hash, hash_value)


def generate_api_key() -> str:
    """Generate API key"""
    return f"stll_{secrets.token_urlsafe(32)}"


def is_safe_url(target: str) -> bool:
    """
    Check if URL is safe for redirect
    
    Args:
        target: URL to check
    
    Returns:
        True if safe, False otherwise
    """
    if not target:
        return False
    
    # Only allow relative URLs or URLs to the same host
    from urllib.parse import urlparse, urljoin
    from flask import request
    
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc


def sanitize_redirect_url(url: str, fallback: str = '/') -> str:
    """
    Sanitize redirect URL
    
    Args:
        url: URL to sanitize
        fallback: Fallback URL if unsafe
    
    Returns:
        Safe URL
    """
    if is_safe_url(url):
        return url
    return fallback


def check_password_policy(password: str) -> Dict[str, Any]:
    """
    Check password against security policy
    
    Args:
        password: Password to check
    
    Returns:
        Dictionary with policy compliance results
    """
    from .validation import validate_password_strength
    return validate_password_strength(password)


def log_security_event(event_type: str, details: Dict[str, Any], user_id: Optional[int] = None):
    """
    Log security-related events
    
    Args:
        event_type: Type of security event
        details: Event details
        user_id: User ID if applicable
    """
    from flask_login import current_user
    
    log_data = {
        'event_type': event_type,
        'timestamp': datetime.utcnow().isoformat(),
        'ip_address': request.remote_addr,
        'user_agent': request.headers.get('User-Agent', ''),
        'user_id': user_id or (current_user.id if current_user.is_authenticated else None),
        'details': details
    }
    
    current_app.logger.warning(f"Security Event: {event_type}", extra=log_data)


def verify_twilio_signature(request_data: bytes, signature: str, auth_token: str, url: str) -> bool:
    """
    Verify Twilio webhook signature
    
    Args:
        request_data: Raw request data
        signature: X-Twilio-Signature header
        auth_token: Twilio auth token
        url: Request URL
    
    Returns:
        True if signature is valid
    """
    import base64
    
    # Create expected signature
    expected = base64.b64encode(
        hmac.new(
            auth_token.encode('utf-8'),
            f"{url}{request_data.decode('utf-8')}".encode('utf-8'),
            hashlib.sha1
        ).digest()
    ).decode('utf-8')
    
    return hmac.compare_digest(expected, signature)


class SecurityHeaders:
    """Security headers management"""
    
    @staticmethod
    def add_security_headers(response):
        """Add security headers to response"""
        # Prevent clickjacking
        response.headers['X-Frame-Options'] = 'DENY'
        
        # Prevent MIME type sniffing
        response.headers['X-Content-Type-Options'] = 'nosniff'
        
        # XSS protection
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        # HTTPS enforcement (if in production)
        if not current_app.debug:
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        # Content Security Policy (basic)
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdnjs.cloudflare.com https://cdn.jsdelivr.net https://code.jquery.com https://unpkg.com; "
            "style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com https://cdn.jsdelivr.net https://fonts.googleapis.com https://unpkg.com; "
            "img-src 'self' data: https:; "
            "font-src 'self' data: https://cdnjs.cloudflare.com https://cdn.jsdelivr.net https://fonts.gstatic.com; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )
        response.headers['Content-Security-Policy'] = csp
        
        return response


def audit_trail(action: str, resource_type: str, resource_id: Optional[int] = None, 
                old_values: Optional[Dict] = None, new_values: Optional[Dict] = None):
    """
    Create audit trail entry
    
    Args:
        action: Action performed (create, update, delete)
        resource_type: Type of resource (user, property, task, etc.)
        resource_id: ID of the resource
        old_values: Previous values (for updates)
        new_values: New values (for creates/updates)
    """
    from flask_login import current_user
    
    audit_data = {
        'action': action,
        'resource_type': resource_type,
        'resource_id': resource_id,
        'user_id': current_user.id if current_user.is_authenticated else None,
        'timestamp': datetime.utcnow().isoformat(),
        'ip_address': request.remote_addr,
        'user_agent': request.headers.get('User-Agent', ''),
        'old_values': old_values,
        'new_values': new_values
    }
    
    current_app.logger.info(f"Audit: {action} {resource_type}", extra=audit_data)


def require_api_key(f):
    """Decorator to require API key authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key or not api_key.startswith('stll_'):
            abort(401)
        
        # In a real implementation, validate the API key against a database
        # For now, just check the format
        if len(api_key) < 40:
            abort(401)
        
        return f(*args, **kwargs)
    return decorated_function


class SessionManager:
    """Enhanced session management for security"""
    
    @staticmethod
    def invalidate_user_sessions(user_id: int):
        """Invalidate all sessions for a specific user"""
        # This would require Redis or database-backed sessions for full implementation
        # For now, we can only clear the current session
        if 'user_id' in session and session['user_id'] == user_id:
            session.clear()
            current_app.logger.info(f"Session invalidated for user {user_id}")
    
    @staticmethod
    def regenerate_session_id():
        """Regenerate session ID to prevent session fixation"""
        # Save important session data
        user_data = {}
        if 'user_id' in session:
            user_data['user_id'] = session['user_id']
        if '_user_id' in session:
            user_data['_user_id'] = session['_user_id']
        if 'remember_token' in session:
            user_data['remember_token'] = session['remember_token']
        
        # Clear session and regenerate
        session.clear()
        session.permanent = True
        
        # Restore important data
        for key, value in user_data.items():
            session[key] = value
        
        current_app.logger.debug("Session ID regenerated")
    
    @staticmethod
    def validate_session_integrity():
        """Validate session integrity"""
        # Check for session hijacking indicators
        user_agent = request.headers.get('User-Agent', '')
        remote_addr = request.remote_addr
        
        # Store fingerprint in session on first visit
        if 'session_fingerprint' not in session:
            session['session_fingerprint'] = {
                'user_agent_hash': hashlib.sha256(user_agent.encode()).hexdigest()[:16],
                'creation_time': time.time()
            }
        
        # Validate fingerprint
        stored_fingerprint = session.get('session_fingerprint', {})
        current_ua_hash = hashlib.sha256(user_agent.encode()).hexdigest()[:16]
        
        if stored_fingerprint.get('user_agent_hash') != current_ua_hash:
            current_app.logger.warning(f"Session fingerprint mismatch for session")
            return False
        
        # Check session age (max 24 hours)
        creation_time = stored_fingerprint.get('creation_time', 0)
        if time.time() - creation_time > 86400:  # 24 hours
            current_app.logger.warning("Session expired due to age")
            return False
        
        return True
    
    @staticmethod
    def secure_session_setup():
        """Set up secure session parameters"""
        session.permanent = True
        
        # Add session security metadata
        if 'session_created' not in session:
            session['session_created'] = time.time()
        
        session['last_activity'] = time.time()


def secure_session_required(f):
    """Decorator to require secure session validation"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not SessionManager.validate_session_integrity():
            session.clear()
            flash('Your session has expired for security reasons. Please log in again.', 'warning')
            return redirect(url_for('auth.login'))
        
        # Update last activity
        session['last_activity'] = time.time()
        
        return f(*args, **kwargs)
    return decorated_function