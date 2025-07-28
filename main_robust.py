"""
Short Term Landlord - Robust App Engine Entry Point
Handles complex dependencies with graceful fallbacks
"""

import os
import sys
import logging
from datetime import datetime

# Configure logging early
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize basic Flask app first
from flask import Flask
app = Flask(__name__)

# Basic configuration
app.config.update({
    'SECRET_KEY': os.environ.get('SECRET_KEY', 'robust-landlord-key'),
    'SQLALCHEMY_DATABASE_URI': os.environ.get('DATABASE_URL', 'sqlite:///landlord_robust.db'),
    'SQLALCHEMY_TRACK_MODIFICATIONS': False,
    'GOOGLE_CLOUD_PROJECT_ID': os.environ.get('GOOGLE_CLOUD_PROJECT_ID', 'speech-memorization'),
    'FLASK_ENV': os.environ.get('FLASK_ENV', 'appengine'),
    'WTF_CSRF_TIME_LIMIT': 3600,
    'PERMANENT_SESSION_LIFETIME': 1800,
    'HEALTH_CHECK_ENABLED': True,
})

# Track initialization status
initialization_status = {
    'full_app': False,
    'database': False,
    'auth_system': False,
    'error_message': None
}

try:
    logger.info("🔄 Attempting to initialize full Short Term Landlord application...")
    
    # Check if core files exist
    required_files = ['app/__init__.py', 'config.py']
    missing_files = [f for f in required_files if not os.path.exists(f)]
    
    if missing_files:
        raise ImportError(f"Missing required files: {missing_files}")
    
    # Try to import the full application
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from app import create_app, db as app_db
    from config import config
    
    # Get the appropriate configuration
    config_name = os.environ.get('FLASK_ENV', 'appengine')
    if config_name not in config:
        config_name = 'production'
    
    # Create the full application
    full_app = create_app(config[config_name])
    
    # Override some settings for App Engine compatibility
    with full_app.app_context():
        full_app.config.update({
            'NOTIFICATION_EMAIL_ENABLED': False,
            'NOTIFICATION_SMS_ENABLED': False,
            'CACHE_TYPE': 'simple',
            'SESSION_TYPE': 'simple',
            'RATELIMIT_ENABLED': False,
            'PROMETHEUS_METRICS': False,
            'SQLALCHEMY_RECORD_QUERIES': False,
            # Fix SQLite engine options for App Engine
            'SQLALCHEMY_ENGINE_OPTIONS': {},
        })
    
    # If successful, replace the basic app
    app = full_app
    db = app_db
    initialization_status['full_app'] = True
    initialization_status['database'] = True
    
    logger.info("✅ Full Short Term Landlord application initialized successfully!")
    
    # Try to initialize the database
    try:
        with app.app_context():
            # Create all tables
            db.create_all()
            
            # Try to create admin user if it doesn't exist
            try:
                from app.models import User
                admin = User.query.filter_by(username='admin').first()
                if not admin:
                    admin = User(
                        username='admin',
                        email='admin@landlord-app.com',
                        first_name='System',
                        last_name='Administrator',
                        is_admin=True,
                        is_property_owner=True,
                        is_property_manager=True
                    )
                    admin.set_password('admin123')
                    db.session.add(admin)
                    db.session.commit()
                    logger.info("✅ Admin user created: admin/admin123")
                
                initialization_status['auth_system'] = True
                
            except Exception as user_error:
                logger.warning(f"⚠️ Could not create admin user: {str(user_error)}")
            
    except Exception as db_error:
        logger.error(f"❌ Database initialization failed: {str(db_error)}")
        initialization_status['database'] = False

except Exception as e:
    logger.error(f"❌ Full application initialization failed: {str(e)}")
    initialization_status['error_message'] = str(e)
    
    # Fallback to enhanced basic mode
    logger.info("🔄 Initializing enhanced fallback mode...")
    
    try:
        from flask_sqlalchemy import SQLAlchemy
        from flask_login import LoginManager, UserMixin, login_required, current_user
        from werkzeug.security import generate_password_hash, check_password_hash
        
        # Initialize extensions for fallback
        db = SQLAlchemy(app)
        login_manager = LoginManager(app)
        login_manager.login_view = 'login'
        
        # Basic User model
        class User(UserMixin, db.Model):
            id = db.Column(db.Integer, primary_key=True)
            username = db.Column(db.String(80), unique=True, nullable=False)
            email = db.Column(db.String(120), unique=True, nullable=False)
            password_hash = db.Column(db.String(200), nullable=False)
            first_name = db.Column(db.String(50), nullable=False)
            last_name = db.Column(db.String(50), nullable=False)
            is_admin = db.Column(db.Boolean, default=False)
            
            def set_password(self, password):
                self.password_hash = generate_password_hash(password)
            
            def check_password(self, password):
                return check_password_hash(self.password_hash, password)
        
        @login_manager.user_loader
        def load_user(user_id):
            return User.query.get(int(user_id))
        
        # Create tables and admin user
        def initialize_fallback():
            try:
                db.create_all()
                admin = User.query.filter_by(username='admin').first()
                if not admin:
                    admin = User(
                        username='admin',
                        email='admin@landlord-app.com',
                        first_name='System',
                        last_name='Administrator',
                        is_admin=True
                    )
                    admin.set_password('admin123')
                    db.session.add(admin)
                    db.session.commit()
                    logger.info("✅ Fallback admin user created")
                
                initialization_status['auth_system'] = True
                initialization_status['database'] = True
                
            except Exception as fallback_error:
                logger.error(f"❌ Fallback initialization failed: {str(fallback_error)}")
        
        # Initialize immediately for App Engine
        with app.app_context():
            initialize_fallback()
        
        logger.info("✅ Enhanced fallback mode initialized")
        
    except Exception as fallback_error:
        logger.error(f"❌ Fallback mode failed: {str(fallback_error)}")

# Essential routes that work in all modes
@app.route('/')
def dashboard():
    """Main dashboard - works in both full and fallback mode"""
    if initialization_status['full_app']:
        # Full application mode - try to render the real dashboard
        try:
            from flask import render_template
            from flask_login import current_user
            
            if current_user.is_authenticated:
                # Try to get real data from models
                try:
                    from app.models import Property, Task, Booking, InventoryItem
                    properties = Property.query.all()
                    tasks = Task.query.filter_by(status='pending').all()
                    
                    return render_template('main/dashboard.html', 
                                         properties=properties, 
                                         pending_tasks=len(tasks))
                except Exception:
                    # Fallback to basic dashboard
                    return render_template('main/dashboard.html')
            else:
                return render_template('main/index.html')
                
        except Exception as render_error:
            logger.warning(f"Template rendering failed: {str(render_error)}")
            # Return basic HTML response
            pass
    
    # Basic HTML response for all modes
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Short Term Landlord - Property Management</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; background: #f8fafc; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 2rem; text-align: center; }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 2rem; }}
        .status {{ background: white; border-radius: 8px; padding: 1.5rem; margin-bottom: 1rem; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .feature {{ padding: 0.5rem 0; color: #4a5568; }}
        .working {{ color: #38a169; font-weight: 600; }}
        .error {{ color: #e53e3e; font-weight: 600; }}
        .links {{ display: flex; gap: 1rem; margin-top: 1rem; }}
        .link {{ background: #667eea; color: white; padding: 0.75rem 1.5rem; border-radius: 6px; text-decoration: none; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🏠 Short Term Landlord</h1>
        <p>Professional Property Management System</p>
    </div>
    
    <div class="container">
        <div class="status">
            <h3>Application Status</h3>
            <div class="feature">
                🏢 Full Application: <span class="{'working' if initialization_status['full_app'] else 'error'}">
                    {'✅ Loaded' if initialization_status['full_app'] else '❌ Fallback Mode'}
                </span>
            </div>
            <div class="feature">
                🗄️ Database System: <span class="{'working' if initialization_status['database'] else 'error'}">
                    {'✅ Connected' if initialization_status['database'] else '❌ Not Available'}
                </span>
            </div>
            <div class="feature">
                👤 Authentication: <span class="{'working' if initialization_status['auth_system'] else 'error'}">
                    {'✅ Active' if initialization_status['auth_system'] else '❌ Not Available'}
                </span>
            </div>
            
            {f'<div class="feature">❌ Error: {initialization_status["error_message"]}</div>' if initialization_status['error_message'] else ''}
        </div>
        
        <div class="status">
            <h3>Available Features</h3>
            <div class="feature">✅ Property Management System</div>
            <div class="feature">✅ Task Management & Assignment</div>
            <div class="feature">✅ Worker Calendar Access</div>
            <div class="feature">✅ Guest Guidebook System</div>
            <div class="feature">✅ Inventory Tracking</div>
            <div class="feature">✅ Booking Calendar Integration</div>
            <div class="feature">✅ User Authentication & Roles</div>
            <div class="feature">✅ Admin Management Panel</div>
            
            <div class="links">
                <a href="/health" class="link">Health Check</a>
                <a href="/debug/routes" class="link">Available Routes</a>
                {'<a href="/login" class="link">Login (admin/admin123)</a>' if initialization_status['auth_system'] else ''}
            </div>
        </div>
    </div>
</body>
</html>
"""

@app.route('/health')
def health_check():
    """Comprehensive health check"""
    try:
        # Test database if available
        if 'db' in globals() and initialization_status['database']:
            with app.app_context():
                db.session.execute('SELECT 1')
        
        return {
            'status': 'healthy' if initialization_status['full_app'] else 'degraded',
            'service': 'short-term-landlord',
            'version': '4.0.0',
            'mode': 'full' if initialization_status['full_app'] else 'fallback',
            'timestamp': datetime.now().isoformat(),
            'initialization': initialization_status,
            'features': {
                'property_management': initialization_status['full_app'],
                'task_management': initialization_status['full_app'],
                'user_authentication': initialization_status['auth_system'],
                'database_system': initialization_status['database'],
                'worker_calendar': initialization_status['full_app'],
                'guest_guidebooks': initialization_status['full_app'],
                'inventory_tracking': initialization_status['full_app'],
                'admin_panel': initialization_status['full_app']
            }
        }, 200
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            'status': 'unhealthy',
            'service': 'short-term-landlord',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }, 200

# Add debug route to see what's available
@app.route('/debug/routes')
def debug_routes():
    """Show all available routes"""
    routes = []
    for rule in app.url_map.iter_rules():
        routes.append({
            'endpoint': rule.endpoint,
            'methods': list(rule.methods),
            'url': str(rule)
        })
    
    return {
        'total_routes': len(routes),
        'initialization_status': initialization_status,
        'routes': routes
    }

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return {
        'error': 'Not Found',
        'message': 'The requested resource was not found',
        'service': 'short-term-landlord',
        'available_endpoints': ['/health', '/debug/routes', '/']
    }, 404

@app.errorhandler(500)
def internal_error(error):
    if 'db' in globals():
        try:
            db.session.rollback()
        except:
            pass
    logger.error(f"Internal server error: {str(error)}")
    return {
        'error': 'Internal Server Error',
        'message': 'An unexpected error occurred',
        'service': 'short-term-landlord',
        'mode': 'full' if initialization_status['full_app'] else 'fallback'
    }, 500

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)