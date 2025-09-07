"""
Short Term Landlord - Production App Engine Entry Point
Robust version with comprehensive error handling and feature detection
"""

import os
import sys
import logging
from flask import Flask, jsonify, render_template, request, redirect, url_for, flash
from datetime import datetime, timedelta

# Configure logging early
logging.basicConfig(level=logging.INFO)

# Initialize basic Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'production-landlord-key')

# App Engine configuration
app.config.update({
    'SQLALCHEMY_DATABASE_URI': os.environ.get('DATABASE_URL', 'sqlite:///landlord_production.db'),
    'SQLALCHEMY_TRACK_MODIFICATIONS': False,
    'GOOGLE_CLOUD_PROJECT_ID': os.environ.get('GOOGLE_CLOUD_PROJECT_ID', 'speech-memorization'),
    'WTF_CSRF_TIME_LIMIT': int(os.environ.get('WTF_CSRF_TIME_LIMIT', 3600)),
    'PERMANENT_SESSION_LIFETIME': int(os.environ.get('PERMANENT_SESSION_LIFETIME', 1800)),
    'MAX_CONTENT_LENGTH': int(os.environ.get('MAX_CONTENT_LENGTH', 16777216)),
    'HEALTH_CHECK_ENABLED': True,
})

# Global variables to track what's available
APP_MODE = 'basic'
db = None
available_features = {
    'user_auth': False,
    'property_management': False,
    'task_management': False,
    'calendar_integration': False,
    'inventory_system': False,
    'worker_management': False,
    'guest_guidebooks': False,
    'full_dashboard': False
}

# Try to initialize the full application
try:
    app.logger.info("🔄 Attempting to initialize full Short Term Landlord application...")
    
    # First check if all required files exist
    required_files = [
        'app/__init__.py',
        'config.py'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        app.logger.warning(f"⚠️ Missing required files: {missing_files}")
        raise ImportError(f"Missing required files: {missing_files}")
    
    # Try to import the main application
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from app import create_app, db as app_db
        from config import config
        
        # Determine configuration
        config_name = os.environ.get('FLASK_ENV', 'production')
        
        # Create the application with AppEngine config
        if config_name in config:
            app = create_app(config[config_name])
        else:
            app = create_app(config['production'])
        
        db = app_db
        APP_MODE = 'full'
        
        # Update available features
        available_features.update({
            'user_auth': True,
            'property_management': True,
            'task_management': True,
            'calendar_integration': True,
            'inventory_system': True,
            'worker_management': True,
            'guest_guidebooks': True,
            'full_dashboard': True
        })
        
        app.logger.info("✅ Full application initialized successfully!")
        
        # Override some settings for App Engine
        with app.app_context():
            app.config.update({
                'NOTIFICATION_EMAIL_ENABLED': False,
                'NOTIFICATION_SMS_ENABLED': False,
                'CACHE_TYPE': 'simple',
                'SESSION_TYPE': 'filesystem',
                'RATELIMIT_ENABLED': False,
                'PROMETHEUS_METRICS': False,
            })
        
    except Exception as import_error:
        app.logger.error(f"❌ Full application import failed: {str(import_error)}")
        raise import_error
        
except Exception as e:
    app.logger.error(f"❌ Full application initialization failed: {str(e)}")
    app.logger.info("🔄 Initializing enhanced basic mode...")
    
    # Enhanced basic mode with core functionality
    try:
        from flask_sqlalchemy import SQLAlchemy
        from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
        from flask_wtf import FlaskForm
        from wtforms import StringField, TextAreaField, SelectField, PasswordField, SubmitField
        from wtforms.validators import DataRequired, Email, Length
        from werkzeug.security import generate_password_hash, check_password_hash
        import secrets
        
        # Initialize extensions
        db = SQLAlchemy(app)
        login_manager = LoginManager(app)
        login_manager.login_view = 'login'
        login_manager.login_message = 'Please log in to access this page.'
        
        APP_MODE = 'enhanced'
        
        # Enhanced models
        class User(UserMixin, db.Model):
            id = db.Column(db.Integer, primary_key=True)
            username = db.Column(db.String(80), unique=True, nullable=False)
            email = db.Column(db.String(120), unique=True, nullable=False)
            password_hash = db.Column(db.String(200), nullable=False)
            first_name = db.Column(db.String(50), nullable=False)
            last_name = db.Column(db.String(50), nullable=False)
            is_admin = db.Column(db.Boolean, default=False)
            is_property_owner = db.Column(db.Boolean, default=True)
            is_property_manager = db.Column(db.Boolean, default=False)
            theme_preference = db.Column(db.String(20), default='light')
            timezone = db.Column(db.String(50), default='UTC')
            created_at = db.Column(db.DateTime, default=datetime.utcnow)
            last_login = db.Column(db.DateTime)
            
            def set_password(self, password):
                self.password_hash = generate_password_hash(password)
            
            def check_password(self, password):
                return check_password_hash(self.password_hash, password)
            
            @property
            def full_name(self):
                return f"{self.first_name} {self.last_name}"
        
        class Property(db.Model):
            id = db.Column(db.Integer, primary_key=True)
            name = db.Column(db.String(200), nullable=False)
            address = db.Column(db.Text, nullable=False)
            description = db.Column(db.Text)
            property_type = db.Column(db.String(50), default='apartment')
            bedrooms = db.Column(db.Integer, default=1)
            bathrooms = db.Column(db.Integer, default=1)
            max_guests = db.Column(db.Integer, default=2)
            checkin_time = db.Column(db.String(20), default='3:00 PM')
            checkout_time = db.Column(db.String(20), default='11:00 AM')
            cleaning_fee = db.Column(db.Float, default=0.0)
            owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
            guest_access_token = db.Column(db.String(64), unique=True)
            worker_calendar_token = db.Column(db.String(64), unique=True)
            guest_access_enabled = db.Column(db.Boolean, default=True)
            is_active = db.Column(db.Boolean, default=True)
            created_at = db.Column(db.DateTime, default=datetime.utcnow)
            
            # Relationships
            owner = db.relationship('User', backref='properties')
            
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
            created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
            task_type = db.Column(db.String(50), default='cleaning')
            status = db.Column(db.String(20), default='pending')
            priority = db.Column(db.String(20), default='medium')
            estimated_duration = db.Column(db.Integer)  # minutes
            actual_duration = db.Column(db.Integer)
            due_date = db.Column(db.DateTime)
            created_at = db.Column(db.DateTime, default=datetime.utcnow)
            started_at = db.Column(db.DateTime)
            completed_at = db.Column(db.DateTime)
            notes = db.Column(db.Text)
            
            # Relationships
            property = db.relationship('Property', backref='tasks')
            assigned_user = db.relationship('User', foreign_keys=[assigned_user_id], backref='assigned_tasks')
            created_by = db.relationship('User', foreign_keys=[created_by_id], backref='created_tasks')
            
            @property
            def is_overdue(self):
                return self.due_date and self.due_date < datetime.utcnow() and self.status != 'completed'
        
        class Booking(db.Model):
            id = db.Column(db.Integer, primary_key=True)
            property_id = db.Column(db.Integer, db.ForeignKey('property.id'), nullable=False)
            guest_name = db.Column(db.String(200), nullable=False)
            guest_email = db.Column(db.String(200))
            guest_phone = db.Column(db.String(20))
            checkin_date = db.Column(db.Date, nullable=False)
            checkout_date = db.Column(db.Date, nullable=False)
            number_of_guests = db.Column(db.Integer, default=1)
            total_amount = db.Column(db.Float, default=0.0)
            status = db.Column(db.String(20), default='confirmed')
            booking_platform = db.Column(db.String(50), default='direct')
            special_requests = db.Column(db.Text)
            created_at = db.Column(db.DateTime, default=datetime.utcnow)
            
            # Relationships
            property = db.relationship('Property', backref='bookings')
            
            @property
            def duration_nights(self):
                return (self.checkout_date - self.checkin_date).days
            
            @property
            def is_current(self):
                today = datetime.now().date()
                return self.checkin_date <= today <= self.checkout_date
        
        class InventoryItem(db.Model):
            id = db.Column(db.Integer, primary_key=True)
            name = db.Column(db.String(200), nullable=False)
            category = db.Column(db.String(100), nullable=False)
            property_id = db.Column(db.Integer, db.ForeignKey('property.id'), nullable=False)
            current_quantity = db.Column(db.Integer, default=0)
            minimum_quantity = db.Column(db.Integer, default=1)
            unit = db.Column(db.String(20), default='each')
            cost_per_unit = db.Column(db.Float, default=0.0)
            supplier = db.Column(db.String(200))
            notes = db.Column(db.Text)
            last_restocked = db.Column(db.DateTime)
            created_at = db.Column(db.DateTime, default=datetime.utcnow)
            
            # Relationships
            property = db.relationship('Property', backref='inventory_items')
            
            @property
            def is_low_stock(self):
                return self.current_quantity <= self.minimum_quantity
        
        class GuidebookEntry(db.Model):
            id = db.Column(db.Integer, primary_key=True)
            property_id = db.Column(db.Integer, db.ForeignKey('property.id'), nullable=False)
            title = db.Column(db.String(200), nullable=False)
            description = db.Column(db.Text)
            category = db.Column(db.String(50), nullable=False)
            address = db.Column(db.Text)
            phone = db.Column(db.String(20))
            website = db.Column(db.String(500))
            hours = db.Column(db.String(200))
            price_range = db.Column(db.String(20))
            rating = db.Column(db.Float)
            is_recommended = db.Column(db.Boolean, default=True)
            sort_order = db.Column(db.Integer, default=0)
            created_at = db.Column(db.DateTime, default=datetime.utcnow)
            
            # Relationships
            property = db.relationship('Property', backref='guidebook_entries')
        
        @login_manager.user_loader
        def load_user(user_id):
            return User.query.get(int(user_id))
        
        # Update available features
        available_features.update({
            'user_auth': True,
            'property_management': True,
            'task_management': True,
            'inventory_system': True,
            'guest_guidebooks': True,
            'worker_management': True,
            'full_dashboard': True
        })
        
        app.logger.info("✅ Enhanced basic mode initialized successfully!")
        
    except Exception as basic_error:
        app.logger.error(f"❌ Enhanced basic mode failed: {str(basic_error)}")
        APP_MODE = 'minimal'
        available_features = {'user_auth': False, 'property_management': False}

# Initialize database and sample data
@app.before_first_request
def initialize_database():
    """Initialize database with sample data"""
    try:
        if db:
            with app.app_context():
                # Create all tables
                db.create_all()
                
                if APP_MODE in ['enhanced', 'full']:
                    from datetime import date
                    
                    # Create admin user
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
                        db.session.flush()
                        
                        # Create sample properties
                        properties = [
                            Property(
                                name='Downtown Loft',
                                address='123 Main Street, Downtown District',
                                description='Modern loft apartment with city views, perfect for business travelers and couples.',
                                property_type='apartment',
                                bedrooms=1,
                                bathrooms=1,
                                max_guests=2,
                                cleaning_fee=75.0,
                                owner_id=admin.id
                            ),
                            Property(
                                name='Suburban Family House',
                                address='456 Oak Avenue, Peaceful Suburbs',
                                description='Spacious family home with backyard, ideal for families and longer stays.',
                                property_type='house',
                                bedrooms=3,
                                bathrooms=2,
                                max_guests=6,
                                cleaning_fee=125.0,
                                owner_id=admin.id
                            ),
                            Property(
                                name='Beachfront Condo',
                                address='789 Ocean Drive, Coastal Area',
                                description='Beautiful oceanfront condo with stunning sunset views and beach access.',
                                property_type='condo',
                                bedrooms=2,
                                bathrooms=2,
                                max_guests=4,
                                cleaning_fee=100.0,
                                owner_id=admin.id
                            )
                        ]
                        
                        for prop in properties:
                            prop.generate_tokens()
                            db.session.add(prop)
                        
                        db.session.flush()
                        
                        # Create sample tasks
                        tasks = [
                            Task(
                                title='Deep clean after checkout',
                                description='Complete cleaning including linens, bathroom deep clean, kitchen sanitization',
                                property_id=1,
                                created_by_id=admin.id,
                                task_type='cleaning',
                                status='pending',
                                priority='high',
                                estimated_duration=120,
                                due_date=datetime.now() + timedelta(hours=2)
                            ),
                            Task(
                                title='Restock bathroom supplies',
                                description='Check and restock toilet paper, towels, soap, shampoo',
                                property_id=1,
                                created_by_id=admin.id,
                                task_type='restocking',
                                status='completed',
                                priority='medium',
                                estimated_duration=30,
                                actual_duration=25,
                                completed_at=datetime.now() - timedelta(hours=6)
                            ),
                            Task(
                                title='Weekly property inspection',
                                description='Check all systems, appliances, and overall property condition',
                                property_id=2,
                                created_by_id=admin.id,
                                task_type='inspection',
                                status='in_progress',
                                priority='medium',
                                estimated_duration=60,
                                started_at=datetime.now() - timedelta(minutes=15)
                            )
                        ]
                        
                        for task in tasks:
                            db.session.add(task)
                        
                        # Create sample bookings
                        bookings = [
                            Booking(
                                property_id=1,
                                guest_name='John & Sarah Smith',
                                guest_email='john.smith@email.com',
                                guest_phone='+1-555-0123',
                                checkin_date=date.today() + timedelta(days=1),
                                checkout_date=date.today() + timedelta(days=4),
                                number_of_guests=2,
                                total_amount=450.0,
                                booking_platform='airbnb'
                            ),
                            Booking(
                                property_id=2,
                                guest_name='The Johnson Family',
                                guest_email='johnson.family@email.com',
                                checkin_date=date.today() + timedelta(days=3),
                                checkout_date=date.today() + timedelta(days=10),
                                number_of_guests=4,
                                total_amount=875.0,
                                booking_platform='vrbo'
                            ),
                            Booking(
                                property_id=3,
                                guest_name='Mike Rodriguez',
                                guest_email='mike.r@email.com',
                                checkin_date=date.today() - timedelta(days=2),
                                checkout_date=date.today() + timedelta(days=3),
                                number_of_guests=1,
                                total_amount=600.0,
                                status='current'
                            )
                        ]
                        
                        for booking in bookings:
                            db.session.add(booking)
                        
                        # Create sample inventory
                        inventory_items = [
                            InventoryItem(
                                name='Toilet Paper',
                                category='bathroom',
                                property_id=1,
                                current_quantity=8,
                                minimum_quantity=4,
                                unit='rolls',
                                cost_per_unit=1.25
                            ),
                            InventoryItem(
                                name='Coffee K-Cups',
                                category='kitchen',
                                property_id=1,
                                current_quantity=12,
                                minimum_quantity=6,
                                unit='pods',
                                cost_per_unit=0.75
                            ),
                            InventoryItem(
                                name='Bath Towels',
                                category='bathroom',
                                property_id=2,
                                current_quantity=2,
                                minimum_quantity=4,
                                unit='each',
                                cost_per_unit=15.00
                            )
                        ]
                        
                        for item in inventory_items:
                            db.session.add(item)
                        
                        # Create sample guidebook entries
                        guidebook_entries = [
                            GuidebookEntry(
                                property_id=1,
                                title='Downtown Brewing Company',
                                description='Local craft brewery with excellent beer selection and pub food.',
                                category='restaurants',
                                address='234 Brewery Street',
                                phone='(555) 123-BREW',
                                website='https://downtownbrewing.com',
                                hours='Mon-Thu 4PM-11PM, Fri-Sun 12PM-12AM',
                                price_range='$$',
                                rating=4.5
                            ),
                            GuidebookEntry(
                                property_id=1,
                                title='City Art Museum',
                                description='Contemporary art museum featuring local and international artists.',
                                category='attractions',
                                address='567 Culture Boulevard',
                                phone='(555) ART-MUSEUM',
                                website='https://cityartmuseum.org',
                                hours='Tue-Sun 10AM-6PM, Closed Mondays',
                                price_range='$',
                                rating=4.2
                            )
                        ]
                        
                        for entry in guidebook_entries:
                            db.session.add(entry)
                        
                        db.session.commit()
                        app.logger.info("✅ Sample data created successfully!")
                        app.logger.info("🔑 Demo login: admin / admin123")
        
    except Exception as e:
        app.logger.error(f"❌ Database initialization failed: {str(e)}")
        if db:
            try:
                db.session.rollback()
            except:
                pass

# Routes will be added based on the APP_MODE in the next part...

# Essential endpoints
@app.route('/health')
def health_check():
    """Comprehensive health check"""
    try:
        # Test database
        if db:
            with app.app_context():
                db.session.execute('SELECT 1')
        
        return {
            'status': 'healthy',
            'service': 'short-term-landlord',
            'version': '2.1.0',
            'mode': APP_MODE,
            'timestamp': datetime.now().isoformat(),
            'features': available_features,
            'database': 'connected' if db else 'unavailable'
        }, 200
        
    except Exception as e:
        app.logger.error(f"Health check failed: {str(e)}")
        return {
            'status': 'degraded',
            'service': 'short-term-landlord',
            'error': str(e),
            'mode': APP_MODE,
            'timestamp': datetime.now().isoformat()
        }, 200

@app.route('/service-info')
def service_info():
    """Detailed service information"""
    return {
        'service_name': 'Short Term Landlord',
        'service_id': 'short-term-landlord',
        'deployment': 'Google App Engine Service',
        'project': os.environ.get('GOOGLE_CLOUD_PROJECT_ID', 'speech-memorization'),
        'version': '2.1.0',
        'mode': APP_MODE,
        'status': 'operational',
        'available_features': available_features,
        'endpoints': {
            '/': 'Main dashboard',
            '/login': 'User authentication' if available_features['user_auth'] else 'Not available',
            '/properties': 'Property management' if available_features['property_management'] else 'Not available',
            '/tasks': 'Task management' if available_features['task_management'] else 'Not available',
            '/inventory': 'Inventory system' if available_features['inventory_system'] else 'Not available',
            '/health': 'Health check',
            '/service-info': 'Service information'
        },
        'demo_access': {
            'username': 'admin',
            'password': 'admin123',
            'note': 'Full access demo account'
        } if APP_MODE in ['enhanced', 'full'] else None,
        'database_tables': db.metadata.tables.keys() if db else []
    }

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)