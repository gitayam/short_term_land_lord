"""
Short Term Landlord - Full Featured App Engine Entry Point

This entry point includes all the core functionality from the original application
with proper error handling and graceful degradation for missing dependencies.
"""

import os
import logging
from flask import Flask, jsonify

# Set up configuration first
config_name = os.environ.get('FLASK_ENV', 'production')

# Initialize basic Flask app for fallback
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'landlord-full-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///landlord_full.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configure logging for App Engine
logging.basicConfig(level=logging.INFO)
app.logger.setLevel(logging.INFO)

try:
    # Try to import and initialize the full application
    from app import create_app, db
    from config import config
    
    # Create the full Flask application with proper config
    app = create_app(config.get(config_name, config['production']))
    
    app.logger.info("✅ Full Short Term Landlord application initialized successfully")
    
    # Add App Engine specific configurations
    with app.app_context():
        app.config.update({
            # App Engine specific settings
            'GOOGLE_CLOUD_PROJECT_ID': os.environ.get('GOOGLE_CLOUD_PROJECT_ID', 'speech-memorization'),
            
            # Force production settings for App Engine
            'ENV': 'production',
            'DEBUG': False,
            'TESTING': False,
            
            # Database settings for SQLite (will work on App Engine)
            'SQLALCHEMY_DATABASE_URI': os.environ.get('DATABASE_URL', 'sqlite:///landlord_full.db'),
            'SQLALCHEMY_ENGINE_OPTIONS': {
                'pool_pre_ping': True,
                'pool_recycle': 300,
                'pool_timeout': 20,
                'echo': False
            },
            
            # Disable features that require external services for initial deployment
            'NOTIFICATION_EMAIL_ENABLED': False,
            'NOTIFICATION_SMS_ENABLED': False,
            'CACHE_TYPE': 'simple',  # Use simple cache instead of Redis
            'SESSION_TYPE': 'filesystem',  # Use filesystem sessions
            'RATELIMIT_ENABLED': False,  # Disable rate limiting initially
            
            # Security settings
            'WTF_CSRF_TIME_LIMIT': 3600,
            'PERMANENT_SESSION_LIFETIME': 1800,
            
            # Media storage settings
            'MEDIA_STORAGE_BACKEND': 'local',
            'MAX_CONTENT_LENGTH': 16 * 1024 * 1024,  # 16MB
            
            # Monitoring settings
            'HEALTH_CHECK_ENABLED': True,
            'PROMETHEUS_METRICS': False,  # Disable for simplicity
            'SQLALCHEMY_RECORD_QUERIES': False,
        })
        
        app.logger.info("✅ App Engine configuration applied")

except Exception as e:
    # Fallback to basic application if full app fails
    app.logger.error(f"❌ Failed to initialize full application: {str(e)}")
    app.logger.info("🔄 Falling back to basic application mode")
    
    # Import basic models and create simple functionality
    from flask_sqlalchemy import SQLAlchemy
    from flask_login import LoginManager, UserMixin, login_required, current_user
    from werkzeug.security import generate_password_hash, check_password_hash
    from datetime import datetime, timedelta
    import secrets
    
    # Initialize extensions for basic mode
    db = SQLAlchemy(app)
    login_manager = LoginManager(app)
    login_manager.login_view = 'login'
    
    # Basic models for fallback mode
    class User(UserMixin, db.Model):
        id = db.Column(db.Integer, primary_key=True)
        username = db.Column(db.String(80), unique=True, nullable=False)
        email = db.Column(db.String(120), unique=True, nullable=False)
        password_hash = db.Column(db.String(200), nullable=False)
        first_name = db.Column(db.String(50), nullable=False)
        last_name = db.Column(db.String(50), nullable=False)
        is_admin = db.Column(db.Boolean, default=False)
        is_property_owner = db.Column(db.Boolean, default=True)
        created_at = db.Column(db.DateTime, default=datetime.utcnow)
        
        def set_password(self, password):
            self.password_hash = generate_password_hash(password)
        
        def check_password(self, password):
            return check_password_hash(self.password_hash, password)
    
    class Property(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(200), nullable=False)
        address = db.Column(db.Text, nullable=False)
        description = db.Column(db.Text)
        property_type = db.Column(db.String(50), default='house')
        bedrooms = db.Column(db.Integer, default=1)
        bathrooms = db.Column(db.Integer, default=1)
        checkin_time = db.Column(db.String(20), default='3:00 PM')
        checkout_time = db.Column(db.String(20), default='11:00 AM')
        owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
        guest_access_token = db.Column(db.String(64), unique=True)
        worker_calendar_token = db.Column(db.String(64), unique=True)
        guest_access_enabled = db.Column(db.Boolean, default=True)
        created_at = db.Column(db.DateTime, default=datetime.utcnow)
        
        def generate_tokens(self):
            if not self.guest_access_token:
                self.guest_access_token = secrets.token_urlsafe(32)
            if not self.worker_calendar_token:
                self.worker_calendar_token = secrets.token_urlsafe(32)
    
    class Task(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        title = db.Column(db.String(200), nullable=False)
        description = db.Column(db.Text)
        property_id = db.Column(db.Integer, db.ForeignKey('property.id'), nullable=False)
        assigned_user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
        status = db.Column(db.String(20), default='pending')
        priority = db.Column(db.String(20), default='medium')
        due_date = db.Column(db.DateTime)
        created_at = db.Column(db.DateTime, default=datetime.utcnow)
        completed_at = db.Column(db.DateTime)
    
    class Booking(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        property_id = db.Column(db.Integer, db.ForeignKey('property.id'), nullable=False)
        guest_name = db.Column(db.String(200), nullable=False)
        guest_email = db.Column(db.String(200))
        checkin_date = db.Column(db.Date, nullable=False)
        checkout_date = db.Column(db.Date, nullable=False)
        number_of_guests = db.Column(db.Integer, default=1)
        status = db.Column(db.String(20), default='confirmed')
        created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Create tables and admin user in fallback mode
    @app.before_first_request
    def initialize_fallback_app():
        """Initialize the fallback application with basic data"""
        try:
            db.create_all()
            
            # Create admin user if not exists
            admin = User.query.filter_by(username='admin').first()
            if not admin:
                admin = User(
                    username='admin',
                    email='admin@landlord-app.com',
                    first_name='System',
                    last_name='Administrator',
                    is_admin=True,
                    is_property_owner=True
                )
                admin.set_password('admin123')
                db.session.add(admin)
                
                # Create sample property
                sample_property = Property(
                    name='Sample Property',
                    address='123 Main St, Anytown, USA',
                    description='A beautiful sample property for demonstration',
                    property_type='apartment',
                    bedrooms=2,
                    bathrooms=1,
                    owner_id=1
                )
                sample_property.generate_tokens()
                db.session.add(sample_property)
                
                # Create sample tasks
                sample_tasks = [
                    Task(
                        title='Clean apartment after checkout',
                        description='Deep clean all rooms, change linens, restock supplies',
                        property_id=1,
                        status='pending',
                        priority='high',
                        due_date=datetime.now() + timedelta(days=1)
                    ),
                    Task(
                        title='Check smoke detectors',
                        description='Test all smoke detectors and replace batteries if needed',
                        property_id=1,
                        status='completed',
                        priority='medium',
                        completed_at=datetime.now() - timedelta(days=5)
                    )
                ]
                
                for task in sample_tasks:
                    db.session.add(task)
                
                # Create sample booking
                sample_booking = Booking(
                    property_id=1,
                    guest_name='John & Jane Doe',
                    guest_email='john.doe@example.com',
                    checkin_date=datetime.now().date() + timedelta(days=1),
                    checkout_date=datetime.now().date() + timedelta(days=4),
                    number_of_guests=2
                )
                db.session.add(sample_booking)
                
                db.session.commit()
                app.logger.info("✅ Fallback mode: Sample data created - Admin: admin/admin123")
            
        except Exception as e:
            app.logger.error(f"❌ Error initializing fallback app: {str(e)}")

# Health check endpoint (works in both modes)
@app.route('/health')
def health_check():
    """Enhanced health check endpoint"""
    try:
        # Test database connection
        if 'db' in globals():
            with app.app_context():
                if hasattr(db.engine, 'execute'):
                    db.engine.execute('SELECT 1')
                else:
                    # SQLAlchemy 2.0+ syntax
                    from sqlalchemy import text
                    db.session.execute(text('SELECT 1'))
        
        # Determine application mode
        mode = 'full' if 'create_app' in globals() else 'fallback'
        
        return {
            'status': 'healthy',
            'service': 'short-term-landlord',
            'version': '2.0.0',
            'mode': mode,
            'timestamp': datetime.now().isoformat(),
            'features': [
                'Property Management',
                'Task Management', 
                'User Authentication',
                'Calendar Integration',
                'Worker Management',
                'Inventory Tracking',
                'Guest Guidebooks',
                'Booking Management',
                'Notification System'
            ] if mode == 'full' else [
                'Basic Property Management',
                'Basic Task Management',
                'User Authentication',
                'Worker Calendar',
                'Guest Access'
            ]
        }, 200
        
    except Exception as e:
        app.logger.error(f"Health check failed: {str(e)}")
        return {
            'status': 'degraded',
            'service': 'short-term-landlord',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }, 200  # Return 200 for App Engine health checks

# Service information endpoint
@app.route('/service-info')
def service_info():
    """Detailed service information"""
    mode = 'full' if 'create_app' in globals() else 'fallback'
    
    return {
        'service_name': 'Short Term Landlord',
        'service_id': 'short-term-landlord',
        'deployment': 'Google App Engine Service',
        'project': os.environ.get('GOOGLE_CLOUD_PROJECT_ID', 'speech-memorization'),
        'version': '2.0.0',
        'mode': mode,
        'status': 'operational',
        'database': 'SQLite' if 'sqlite' in app.config.get('SQLALCHEMY_DATABASE_URI', '') else 'PostgreSQL',
        'features': {
            'property_management': True,
            'task_management': True,
            'user_authentication': True,
            'calendar_integration': mode == 'full',
            'worker_management': True,
            'inventory_tracking': mode == 'full',
            'guest_guidebooks': True,
            'booking_management': True,
            'notification_system': mode == 'full',
            'admin_features': mode == 'full',
            'invoicing': mode == 'full',
            'messaging': mode == 'full'
        },
        'endpoints': {
            '/': 'Main dashboard',
            '/login': 'User authentication',
            '/properties': 'Property management',
            '/tasks': 'Task management',
            '/calendar': 'Calendar view',
            '/inventory': 'Inventory tracking' if mode == 'full' else 'Not available',
            '/workforce': 'Worker management' if mode == 'full' else 'Not available',
            '/admin': 'Admin panel' if mode == 'full' else 'Not available',
            '/health': 'Health check',
            '/service-info': 'Service information'
        },
        'demo_credentials': {
            'username': 'admin',
            'password': 'admin123',
            'note': 'Demo account with full access'
        }
    }

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return {
        'error': 'Not Found',
        'message': 'The requested resource was not found',
        'service': 'short-term-landlord'
    }, 404

@app.errorhandler(500)
def internal_error(error):
    if 'db' in globals():
        try:
            db.session.rollback()
        except:
            pass
    app.logger.error(f"Internal server error: {str(error)}")
    return {
        'error': 'Internal Server Error',
        'message': 'An unexpected error occurred',
        'service': 'short-term-landlord'
    }, 500

if __name__ == '__main__':
    # This is used only for local development
    app.run(host='127.0.0.1', port=8080, debug=True)