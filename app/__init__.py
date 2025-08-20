from flask import Flask, jsonify, g, request
from .utils.route_debug import list_routes
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
# Optional imports for production features
try:
    from flask_caching import Cache
    CACHING_AVAILABLE = True
except ImportError:
    Cache = None
    CACHING_AVAILABLE = False

try:
    from flask_session import Session
    SESSION_AVAILABLE = True
except ImportError:
    Session = None
    SESSION_AVAILABLE = False
from config import Config
from .utils.security import SecurityHeaders
import os
import time
import uuid

from app.user_model_fix import patch_user_model, patch_user_loader

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
mail = Mail()
migrate = Migrate()
csrf = CSRFProtect()
cache = Cache() if CACHING_AVAILABLE else None
session_store = Session() if SESSION_AVAILABLE else None

def create_app(config_class=Config):
    app = Flask(__name__)
    
    # Handle both string and class inputs for config_class
    if isinstance(config_class, str):
        if config_class == 'testing':
            from config import TestConfig
            app.config.from_object(TestConfig)
        elif config_class.startswith('postgres'):
            # Handle PostgreSQL configurations
            if config_class == 'postgres_dev':
                from config_postgres import DevelopmentPostgreSQLConfig
                app.config.from_object(DevelopmentPostgreSQLConfig)
            elif config_class == 'postgres_prod':
                from config_postgres import ProductionPostgreSQLConfig
                app.config.from_object(ProductionPostgreSQLConfig)
            elif config_class == 'postgres_test':
                from config_postgres import TestPostgreSQLConfig
                app.config.from_object(TestPostgreSQLConfig)
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
    csrf.init_app(app)
    if cache:
        cache.init_app(app)
    if session_store:
        session_store.init_app(app)
    
    # Initialize production monitoring if enabled
    if app.config.get('SENTRY_DSN'):
        setup_sentry(app)
    
    if app.config.get('PROMETHEUS_METRICS'):
        setup_prometheus(app)
    
    # Setup performance monitoring
    setup_performance_monitoring(app)
    
    # Setup request context
    setup_request_context(app)
    
    # Initialize task permission functions for templates
    try:
        from app.tasks.routes import can_view_task, can_edit_task, can_delete_task, can_complete_task
        app.jinja_env.globals.update(
            can_view_task=can_view_task,
            can_edit_task=can_edit_task,
            can_delete_task=can_delete_task,
            can_complete_task=can_complete_task
        )
    except ImportError as e:
        app.logger.warning(f"Could not import task permission functions: {e}")
        # Provide fallback functions
        def fallback_permission_func(*args, **kwargs):
            return True
        app.jinja_env.globals.update(
            can_view_task=fallback_permission_func,
            can_edit_task=fallback_permission_func,
            can_delete_task=fallback_permission_func,
            can_complete_task=fallback_permission_func
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
    
    # Register configuration management blueprint
    from app.admin.config_routes import bp as admin_config_bp
    app.register_blueprint(admin_config_bp)
    
    from app.workforce import bp as workforce_bp
    app.register_blueprint(workforce_bp, url_prefix='/workforce')

    from app.messages import bp as messages_bp
    app.register_blueprint(messages_bp, url_prefix='/messages')

    from app.guidebook import bp as guidebook_bp
    app.register_blueprint(guidebook_bp, url_prefix='/guidebook')

    from app.guest import bp as guest_bp
    app.register_blueprint(guest_bp, url_prefix='/guest')

    from app.routes.health import bp as health_bp
    app.register_blueprint(health_bp)
    
    from app.routes.recommendation_routes import bp as recommendations_bp
    app.register_blueprint(recommendations_bp, url_prefix='/recommendations')
    
    from app.share import bp as share_bp
    app.register_blueprint(share_bp)
    
    from app.routes.property_routes import bp as property_routes_bp
    app.register_blueprint(property_routes_bp)
    
    from app.routes.analytics_routes import bp as analytics_bp
    app.register_blueprint(analytics_bp)
    
    from app.routes.financial_analytics_routes import bp as financial_analytics_bp
    app.register_blueprint(financial_analytics_bp)
    
    from app.errors import bp as errors_bp
    app.register_blueprint(errors_bp)

    # Debug route to list all registered routes
    @app.route('/debug/routes')
    def debug_routes():
        return list_routes()

    # Health check endpoint
    if app.config.get('HEALTH_CHECK_ENABLED'):
        @app.route('/health')
        def health_check():
            from app.utils.health_checks import HealthChecker
            health_checker = HealthChecker()
            results = health_checker.run_all_checks()
            
            status_code = 200
            if results['status'] == 'unhealthy':
                status_code = 503
            elif results['status'] == 'warning':
                status_code = 200
            
            return jsonify(results), status_code

    # Metrics endpoint for Prometheus
    if app.config.get('PROMETHEUS_METRICS'):
        @app.route('/metrics')
        def metrics():
            from prometheus_client import generate_latest
            return generate_latest()

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


def setup_sentry(app):
    """Initialize Sentry for error tracking"""
    try:
        import sentry_sdk
        from sentry_sdk.integrations.flask import FlaskIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
    except ImportError:
        app.logger.warning("Sentry SDK not available - error tracking disabled")
        return
    
    sentry_sdk.init(
        dsn=app.config['SENTRY_DSN'],
        integrations=[
            FlaskIntegration(),
            SqlalchemyIntegration()
        ],
        traces_sample_rate=0.1,  # 10% of transactions
        environment=os.environ.get('FLASK_ENV', 'development')
    )


def setup_prometheus(app):
    """Setup Prometheus metrics collection"""
    try:
        from prometheus_client import Counter, Histogram, Gauge
    except ImportError:
        app.logger.warning("Prometheus client not available - metrics disabled")
        return
    
    # Define metrics
    REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
    REQUEST_LATENCY = Histogram('http_request_duration_seconds', 'HTTP request latency')
    ACTIVE_CONNECTIONS = Gauge('database_connections_active', 'Active database connections')
    
    @app.before_request
    def before_request():
        g.start_time = time.time()
        g.request_id = str(uuid.uuid4())
    
    @app.after_request
    def after_request(response):
        if hasattr(g, 'start_time'):
            request_latency = time.time() - g.start_time
            REQUEST_LATENCY.observe(request_latency)
            REQUEST_COUNT.labels(
                method=request.method,
                endpoint=request.endpoint or 'unknown',
                status=response.status_code
            ).inc()
        return response


def setup_performance_monitoring(app):
    """Setup database query performance monitoring"""
    if app.config.get('SQLALCHEMY_RECORD_QUERIES'):
        from sqlalchemy import event
        from sqlalchemy.engine import Engine
        
        @event.listens_for(Engine, "before_cursor_execute")
        def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            context._query_start_time = time.time()
        
        @event.listens_for(Engine, "after_cursor_execute")
        def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            total = time.time() - context._query_start_time
            threshold = app.config.get('SLOW_QUERY_THRESHOLD', 0.5)
            
            if total > threshold:
                app.logger.warning(
                    f"Slow query detected: {total:.3f}s",
                    extra={
                        'query_time': total,
                        'query': statement[:200] + '...' if len(statement) > 200 else statement,
                        'request_id': getattr(g, 'request_id', None)
                    }
                )


def setup_request_context(app):
    """Setup request context and logging"""
    @app.before_request
    def before_request():
        if not hasattr(g, 'request_id'):
            g.request_id = str(uuid.uuid4())
        
        # Log request start
        app.logger.info(
            f"Request started: {request.method} {request.path}",
            extra={
                'request_id': g.request_id,
                'method': request.method,
                'path': request.path,
                'remote_addr': request.remote_addr,
                'user_agent': request.headers.get('User-Agent', '')
            }
        )
    
    @app.after_request
    def after_request(response):
        # Log request completion
        if hasattr(g, 'request_id'):
            app.logger.info(
                f"Request completed: {response.status_code}",
                extra={
                    'request_id': g.request_id,
                    'status_code': response.status_code,
                    'content_length': response.content_length
                }
            )
        return response