from flask import Flask, jsonify
from .utils.route_debug import list_routes
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from flask_session import Session
from config import Config
from .utils.security import SecurityHeaders
import os
import redis

from app.user_model_fix import patch_user_model, patch_user_loader
# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
mail = Mail()
migrate = Migrate()
csrf = CSRFProtect()
session = Session()

def create_app(config_class=Config):
    app = Flask(__name__)
    
    # Handle both string and class inputs for config_class
    if isinstance(config_class, str):
        if config_class == 'testing':
            from config import TestConfig
            app.config.from_object(TestConfig)
        else:
            # Try to import the config class by name
            app.config.from_object(config_class)
    else:
        app.config.from_object(config_class)
    
    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)
    
    # Configure Redis for session storage
    if app.config.get('SESSION_TYPE') == 'redis':
        try:
            redis_client = redis.from_url(app.config.get('REDIS_URL', 'redis://localhost:6379/0'))
            app.config['SESSION_REDIS'] = redis_client
        except Exception as e:
            app.logger.warning(f"Failed to connect to Redis for sessions: {e}")
            # Fallback to filesystem sessions
            app.config['SESSION_TYPE'] = 'filesystem'
    
    session.init_app(app)
    
    # Configure CSRF protection after session is initialized (only if enabled)
    if app.config.get('WTF_CSRF_ENABLED', True):
        csrf.init_app(app)
        app.logger.info("CSRF protection enabled")
    else:
        app.logger.info("CSRF protection disabled")
    
    # Ensure session interface is properly configured for CSRF
    if hasattr(app, 'session_interface'):
        app.logger.info(f"Session interface configured: {type(app.session_interface).__name__}")
    else:
        app.logger.warning("No session interface configured")
    
    # Initialize task permission functions for templates
    from app.tasks.routes import can_view_task, can_edit_task, can_delete_task, can_complete_task
    app.jinja_env.globals.update(
        can_view_task=can_view_task,
        can_edit_task=can_edit_task,
        can_delete_task=can_delete_task,
        can_complete_task=can_complete_task
    )
    
    # Register custom Jinja2 filters
    @app.template_filter('nl2br')
    def nl2br_filter(s):
        if s:
            return s.replace('\n', '<br>')
        return s
    
    # Register blueprints
    from app.auth import bp as auth_bp
    from app.calendar import bp as calendar_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(calendar_bp, url_prefix='/calendar')
    
    from app.main import bp as main_bp
    app.register_blueprint(main_bp)
    
    from app.profile import bp as profile_bp
    app.register_blueprint(profile_bp, url_prefix='/profile')
    
    from app.property import bp as property_bp
    app.register_blueprint(property_bp, url_prefix='/property')
    
    from app.tasks import bp as tasks_bp
    app.register_blueprint(tasks_bp, url_prefix='/tasks')
    
    from app.notifications import bp as notifications_bp
    app.register_blueprint(notifications_bp, url_prefix='/notifications')
    
    from app.inventory import bp as inventory_bp
    app.register_blueprint(inventory_bp, url_prefix='/inventory')
    
    from app.invoicing import bp as invoicing_bp
    app.register_blueprint(invoicing_bp, url_prefix='/invoicing')
    
    from app.admin import bp as admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    from app.workforce import bp as workforce_bp
    app.register_blueprint(workforce_bp, url_prefix='/workforce')

    from app.messages import bp as messages_bp
    app.register_blueprint(messages_bp, url_prefix='/messages')

    from app.guidebook import bp as guidebook_bp
    app.register_blueprint(guidebook_bp, url_prefix='/guidebook')

    from app.routes.health import bp as health_bp
    app.register_blueprint(health_bp)
    
    from app.routes.recommendation_routes import bp as recommendations_bp
    app.register_blueprint(recommendations_bp, url_prefix='/recommendations')
    
    from app.routes.property_routes import bp as property_routes_bp
    app.register_blueprint(property_routes_bp)
    
    from app.errors import bp as errors_bp
    app.register_blueprint(errors_bp)

    # Debug route to list all registered routes
    @app.route('/debug/routes')
    def debug_routes():
        return list_routes()

    from app.context_processors import admin_properties, user_theme
    app.context_processor(admin_properties)
    app.context_processor(user_theme)
    
    # Fix PostgreSQL transactions if needed
    with app.app_context():
        try:
            # Only run the fix for PostgreSQL databases
            if app.config['SQLALCHEMY_DATABASE_URI'].startswith('postgresql'):
                app.logger.info("Checking PostgreSQL transactions and schema...")
                
                # Import and run the transaction fix script
                from sqlalchemy import text
                
                # Reset any aborted transactions with autocommit isolation
                with db.engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
                    # Find connections in an aborted state
                    result = conn.execute(text("""
                        SELECT pid, state 
                        FROM pg_stat_activity 
                        WHERE state = 'idle in transaction' OR 
                              state = 'idle in transaction (aborted)' OR
                              state = 'active'
                    """))
                    
                    transactions = result.fetchall()
                    
                    if transactions:
                        app.logger.warning(f"Found {len(transactions)} potentially problematic transactions. Resetting them...")
                        for tx in transactions:
                            # Don't terminate our own connection
                            if tx.state != 'active':
                                try:
                                    conn.execute(text(f"SELECT pg_terminate_backend({tx.pid})"))
                                    app.logger.info(f"Terminated connection {tx.pid} in state {tx.state}")
                                except Exception as e:
                                    app.logger.warning(f"Could not terminate connection {tx.pid}: {str(e)}")
                
                app.logger.info("PostgreSQL transaction check completed")
        except Exception as e:
            app.logger.warning(f"Could not check PostgreSQL transactions: {str(e)}")
    
    # Initialize site settings and User model
    with app.app_context():
        try:
            from app.models import migrate_site_settings, create_admin_user_from_env, init_app as init_user_model
            
            # Initialize User model table name
            init_user_model(app)
            
            # Initialize site settings
            migrate_site_settings()
            
            # Create admin user from environment variables if configured
            create_admin_user_from_env()
        except Exception as e:
            # Handle the case where site_settings table doesn't exist yet
            app.logger.warning(f"Could not initialize site settings: {str(e)}")
            app.logger.info("You may need to run 'flask db upgrade' if this is a new installation")
    
    # ADDED: Create all tables if they don't exist
    with app.app_context():
        try:
            from sqlalchemy import inspect
            
            inspector = inspect(db.engine)
            existing_tables = inspector.get_table_names()
            
            if 'property' not in existing_tables:
                app.logger.info("Creating database tables...")
                db.create_all()
                app.logger.info("Database tables successfully created")
            
        except Exception as e:
            app.logger.error(f"Error creating database tables: {str(e)}")
    
    with app.app_context():
        # Apply database compatibility fixes
        patch_user_model()
        patch_user_loader()
        
        # Validate Twilio configuration
        try:
            from app.utils.sms import validate_twilio_config
            is_valid, message = validate_twilio_config()
            if not is_valid:
                app.logger.warning(f"Twilio configuration issue: {message}")
                app.logger.warning("SMS functionality may not work properly")
            else:
                app.logger.info("Twilio configuration validated successfully")
        except Exception as e:
            app.logger.warning(f"Could not validate Twilio configuration: {str(e)}")
    
    # Add security headers to all responses
    @app.after_request
    def add_security_headers(response):
        return SecurityHeaders.add_security_headers(response)
    
    return app

from app import models