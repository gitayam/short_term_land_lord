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
    current_app.logger.warning(f'CSRF validation failed for {request.endpoint}: {error.description}')
    
    # Return JSON for AJAX requests
    if request.is_json or request.headers.get('Content-Type') == 'application/json':
        return jsonify({
            'error': 'CSRF token validation failed',
            'message': 'Security token expired or invalid. Please refresh the page.'
        }), 400
    
    # Return HTML for regular requests
    return render_template('errors/csrf.html', error=error), 400 