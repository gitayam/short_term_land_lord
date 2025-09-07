from flask import Blueprint, jsonify

bp = Blueprint('health', __name__)

@bp.route('/health')
def health_check():
    """Health check endpoint for monitoring and CI/CD."""
    return jsonify({
        'status': 'healthy',
        'version': '1.0.0'
    }), 200 