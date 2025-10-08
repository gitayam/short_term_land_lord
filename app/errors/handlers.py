from flask import render_template, request, jsonify, current_app
from flask_wtf.csrf import CSRFError
from app.errors import bp

@bp.app_errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@bp.app_errorhandler(500)
def internal_error(error):
    return render_template('errors/500.html'), 500

@bp.app_errorhandler(403)
def forbidden_error(error):
    return render_template('errors/403.html'), 403

@bp.app_errorhandler(CSRFError)
def handle_csrf_error(error):
    """Handle CSRF token validation errors"""
    # Safely log the error with proper error handling
    try:
        if current_app and hasattr(current_app, 'logger'):
            current_app.logger.warning(f'CSRF validation failed for {request.endpoint}: {error.description}')
        else:
            # Fallback logging when current_app is not available
            print(f'CSRF validation failed for {getattr(request, "endpoint", "unknown")}: {error.description}')
    except Exception as log_error:
        # Even if logging fails, continue with the response
        print(f'Error logging CSRF failure: {log_error}')
    
    # Return JSON for AJAX requests
    try:
        if request.is_json or request.headers.get('Content-Type') == 'application/json':
            return jsonify({
                'error': 'CSRF token validation failed',
                'message': 'Security token expired or invalid. Please refresh the page.'
            }), 400
    except Exception:
        pass
    
    # Return HTML for regular requests
    try:
        return render_template('errors/csrf.html', error=error), 400
    except Exception:
        # Ultimate fallback - plain text response
        return f'CSRF token validation failed: {error.description}', 400 