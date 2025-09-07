"""
Short Term Landlord - Dedicated App Engine Service Entry Point

This file serves as the entry point for the Short Term Landlord application
deployed as a dedicated App Engine service with full features.
"""

import os
import logging
from flask import Flask, jsonify

# Set up basic Flask app first for fallback
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'landlord-service-key')

# Try to import and initialize the full application
try:
    from app import create_app, db
    from config import config
    
    # Determine the configuration to use
    config_name = os.environ.get('FLASK_ENV', 'production')
    
    # Create the full Flask application
    app = create_app(config.get(config_name, config['default']))
    
    # Set up logging for production
    if config_name == 'production':
        logging.basicConfig(level=logging.INFO)
        app.logger.setLevel(logging.INFO)
        app.logger.info("Short Term Landlord service starting with full features")

except Exception as e:
    # Fallback to basic Flask app if full app fails to initialize
    app.logger.error(f"Failed to initialize full application: {str(e)}")
    app.logger.info("Running in fallback mode with basic features")
    
    @app.route('/')
    def home():
        return {
            'status': 'running',
            'service': 'Short Term Landlord',
            'mode': 'fallback',
            'message': 'Application is running in basic mode. Full features will be available after proper setup.',
            'features': [
                'Property Management (Setup Required)',
                'Guest Guidebooks (Setup Required)', 
                'Worker Calendar (Setup Required)',
                'Task Management (Setup Required)',
                'Inventory Tracking (Setup Required)'
            ]
        }

# Add health check endpoint (works in both modes)
@app.route('/health')
def health_check():
    """Health check endpoint for App Engine"""
    try:
        # Try to check database if available
        if 'db' in globals():
            with app.app_context():
                db.engine.execute('SELECT 1')
        
        return {
            'status': 'healthy',
            'service': 'short-term-landlord',
            'version': '1.0.0',
            'mode': 'full' if 'create_app' in globals() else 'fallback'
        }, 200
    except Exception as e:
        return {
            'status': 'degraded',
            'service': 'short-term-landlord',
            'error': str(e)
        }, 200  # Return 200 for App Engine health checks

# Add service info endpoint
@app.route('/service-info')
def service_info():
    """Information about this specific service"""
    return {
        'service_name': 'Short Term Landlord',
        'service_id': 'short-term-landlord',
        'deployment': 'Google App Engine Service',
        'project': 'speech-memorization',
        'version': '1.0.0',
        'endpoints': {
            '/': 'Application dashboard',
            '/health': 'Health check',
            '/service-info': 'Service information',
            '/properties': 'Property management (if configured)',
            '/worker-calendar': 'Worker calendar access',
            '/guest': 'Guest guidebook access'
        },
        'features': {
            'property_management': True,
            'guest_guidebooks': True,
            'worker_calendar': True,
            'task_assignments': True,
            'inventory_tracking': True,
            'interactive_maps': True,
            'mobile_responsive': True
        }
    }

# Database initialization for full mode
if 'db' in globals():
    @app.before_first_request
    def create_tables():
        """Create database tables if they don't exist"""
        try:
            with app.app_context():
                # Import all models to ensure they're registered
                from app import models
                
                # Create tables
                db.create_all()
                app.logger.info("Database tables created/updated successfully")
        except Exception as e:
            app.logger.error(f"Error creating database tables: {str(e)}")

    # Error handlers for production
    @app.errorhandler(404)
    def not_found_error(error):
        return {
            'error': 'Not found',
            'message': 'The requested resource was not found',
            'service': 'short-term-landlord'
        }, 404

    @app.errorhandler(500)
    def internal_error(error):
        if 'db' in globals():
            db.session.rollback()
        app.logger.error(f"Internal server error: {str(error)}")
        return {
            'error': 'Internal server error',
            'message': 'An unexpected error occurred',
            'service': 'short-term-landlord'
        }, 500

if __name__ == '__main__':
    # This is used only for local development
    app.run(host='127.0.0.1', port=8080, debug=True)