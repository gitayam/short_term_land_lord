"""
Application Performance Monitoring and Metrics Collection

This module provides comprehensive monitoring capabilities including Prometheus metrics,
Sentry error tracking, performance monitoring, and system health checks.
"""

from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from flask import request, g, Response, current_app
import time
import psutil
import os
import logging
from datetime import datetime, timedelta
from functools import wraps
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

logger = logging.getLogger(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter(
    'http_requests_total', 
    'Total HTTP requests', 
    ['method', 'endpoint', 'status_code']
)

REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds', 
    'HTTP request latency in seconds',
    ['method', 'endpoint']
)

ACTIVE_USERS = Gauge(
    'active_users_total', 
    'Number of active users'
)

DATABASE_CONNECTIONS = Gauge(
    'database_connections_active', 
    'Active database connections'
)

SYSTEM_CPU_USAGE = Gauge(
    'system_cpu_usage_percent', 
    'System CPU usage percentage'
)

SYSTEM_MEMORY_USAGE = Gauge(
    'system_memory_usage_percent', 
    'System memory usage percentage'
)

CACHE_HITS = Counter(
    'cache_hits_total', 
    'Total cache hits'
)

CACHE_MISSES = Counter(
    'cache_misses_total', 
    'Total cache misses'
)

TASK_OPERATIONS = Counter(
    'task_operations_total', 
    'Total task operations', 
    ['operation', 'status']
)

PROPERTY_OPERATIONS = Counter(
    'property_operations_total', 
    'Total property operations', 
    ['operation', 'status']
)

USER_OPERATIONS = Counter(
    'user_operations_total', 
    'Total user operations', 
    ['operation', 'status']
)

DATABASE_QUERY_TIME = Histogram(
    'database_query_duration_seconds',
    'Database query execution time',
    ['table', 'operation']
)

ERROR_COUNT = Counter(
    'application_errors_total',
    'Total application errors',
    ['error_type', 'endpoint']
)

class ApplicationMonitor:
    """Main application monitoring class"""
    
    def __init__(self, app=None):
        self.app = app
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize monitoring with Flask app"""
        self.app = app
        self.setup_sentry()
        self.setup_prometheus()
        self.setup_performance_monitoring()
        logger.info("Application monitoring initialized")
    
    def setup_sentry(self):
        """Initialize Sentry for error tracking"""
        sentry_dsn = self.app.config.get('SENTRY_DSN')
        if sentry_dsn:
            try:
                sentry_sdk.init(
                    dsn=sentry_dsn,
                    integrations=[
                        FlaskIntegration(auto_enabling_integrations=False),
                        SqlalchemyIntegration()
                    ],
                    traces_sample_rate=float(self.app.config.get('SENTRY_TRACES_SAMPLE_RATE', 0.1)),
                    environment=self.app.config.get('ENVIRONMENT', 'development'),
                    attach_stacktrace=True,
                    send_default_pii=False
                )
                logger.info("Sentry error tracking initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Sentry: {e}")
        else:
            logger.info("Sentry DSN not configured, skipping error tracking")
    
    def setup_prometheus(self):
        """Setup Prometheus metrics collection"""
        @self.app.before_request
        def before_request():
            g.start_time = time.time()
            g.request_start = datetime.utcnow()
        
        @self.app.after_request
        def after_request(response):
            if hasattr(g, 'start_time'):
                request_latency = time.time() - g.start_time
                
                # Record metrics
                REQUEST_LATENCY.labels(
                    method=request.method,
                    endpoint=request.endpoint or 'unknown'
                ).observe(request_latency)
                
                REQUEST_COUNT.labels(
                    method=request.method,
                    endpoint=request.endpoint or 'unknown',
                    status_code=response.status_code
                ).inc()
                
                # Log slow requests
                if request_latency > 1.0:  # Log requests taking more than 1 second
                    logger.warning(
                        f"Slow request: {request.method} {request.path} "
                        f"took {request_latency:.2f}s"
                    )
            
            return response
        
        @self.app.errorhandler(Exception)
        def handle_error(error):
            ERROR_COUNT.labels(
                error_type=type(error).__name__,
                endpoint=request.endpoint or 'unknown'
            ).inc()
            
            # Log the error
            logger.error(f"Application error: {error}", exc_info=True)
            
            # Re-raise the error so Flask can handle it normally
            raise error
    
    def setup_performance_monitoring(self):
        """Setup performance monitoring hooks"""
        # Monitor database queries if SQLAlchemy is available
        try:
            from sqlalchemy import event
            from sqlalchemy.engine import Engine
            
            @event.listens_for(Engine, "before_cursor_execute")
            def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
                context._query_start_time = time.time()
                context._query_statement = statement
            
            @event.listens_for(Engine, "after_cursor_execute")
            def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
                total = time.time() - context._query_start_time
                
                # Extract table name and operation from SQL
                table_name = 'unknown'
                operation = 'unknown'
                
                statement_lower = statement.lower().strip()
                if statement_lower.startswith('select'):
                    operation = 'select'
                    # Try to extract table name from SELECT
                    if 'from' in statement_lower:
                        try:
                            table_part = statement_lower.split('from')[1].split()[0].strip()
                            table_name = table_part.split('.')[1] if '.' in table_part else table_part
                        except (IndexError, AttributeError):
                            pass
                elif statement_lower.startswith('insert'):
                    operation = 'insert'
                    if 'into' in statement_lower:
                        try:
                            table_name = statement_lower.split('into')[1].split()[0].strip()
                        except (IndexError, AttributeError):
                            pass
                elif statement_lower.startswith('update'):
                    operation = 'update'
                    try:
                        table_name = statement_lower.split('update')[1].split()[0].strip()
                    except (IndexError, AttributeError):
                        pass
                elif statement_lower.startswith('delete'):
                    operation = 'delete'
                    if 'from' in statement_lower:
                        try:
                            table_name = statement_lower.split('from')[1].split()[0].strip()
                        except (IndexError, AttributeError):
                            pass
                
                DATABASE_QUERY_TIME.labels(
                    table=table_name,
                    operation=operation
                ).observe(total)
                
        except ImportError:
            logger.warning("SQLAlchemy not available for database monitoring")
    
    def collect_system_metrics(self):
        """Collect system-level metrics"""
        try:
            # CPU and memory usage
            cpu_percent = psutil.cpu_percent(interval=1)
            memory_percent = psutil.virtual_memory().percent
            
            SYSTEM_CPU_USAGE.set(cpu_percent)
            SYSTEM_MEMORY_USAGE.set(memory_percent)
            
            # Database connections
            active_connections = self.get_db_connection_count()
            if active_connections is not None:
                DATABASE_CONNECTIONS.set(active_connections)
            
            # Active users (last 5 minutes)
            active_users = self.get_active_user_count()
            if active_users is not None:
                ACTIVE_USERS.set(active_users)
            
            return {
                'cpu_percent': cpu_percent,
                'memory_percent': memory_percent,
                'active_connections': active_connections,
                'active_users': active_users,
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            return {}
    
    def get_db_connection_count(self):
        """Get current database connection count"""
        try:
            from app import db
            from sqlalchemy import text
            
            if 'postgresql' in self.app.config.get('SQLALCHEMY_DATABASE_URI', ''):
                result = db.session.execute(text("""
                    SELECT count(*) FROM pg_stat_activity
                    WHERE state = 'active'
                """))
                return result.scalar()
        except Exception as e:
            logger.debug(f"Could not get database connection count: {e}")
        return None
    
    def get_active_user_count(self):
        """Get active user count (users active in last 5 minutes)"""
        try:
            from app.models import User
            five_minutes_ago = datetime.utcnow() - timedelta(minutes=5)
            
            # This assumes you have a last_activity field on User model
            if hasattr(User, 'last_activity'):
                return User.query.filter(
                    User.last_activity >= five_minutes_ago
                ).count()
            elif hasattr(User, 'last_login'):
                return User.query.filter(
                    User.last_login >= five_minutes_ago
                ).count()
        except Exception as e:
            logger.debug(f"Could not get active user count: {e}")
        return None

def monitor_operation(operation_type, operation_name):
    """Decorator to monitor specific operations"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            start_time = time.time()
            status = 'success'
            
            try:
                result = f(*args, **kwargs)
                return result
            except Exception as e:
                status = 'error'
                logger.error(f"Operation {operation_name} failed: {e}")
                raise
            finally:
                duration = time.time() - start_time
                
                # Record operation metrics
                if operation_type == 'task':
                    TASK_OPERATIONS.labels(
                        operation=operation_name,
                        status=status
                    ).inc()
                elif operation_type == 'property':
                    PROPERTY_OPERATIONS.labels(
                        operation=operation_name,
                        status=status
                    ).inc()
                elif operation_type == 'user':
                    USER_OPERATIONS.labels(
                        operation=operation_name,
                        status=status
                    ).inc()
                
                # Log slow operations
                if duration > 2.0:
                    logger.warning(
                        f"Slow {operation_type} operation {operation_name}: {duration:.2f}s"
                    )
        
        return decorated_function
    return decorator

def record_cache_hit():
    """Record cache hit metric"""
    CACHE_HITS.inc()

def record_cache_miss():
    """Record cache miss metric"""
    CACHE_MISSES.inc()

def create_metrics_endpoint(app):
    """Create /metrics endpoint for Prometheus"""
    @app.route('/metrics')
    def metrics():
        """Prometheus metrics endpoint"""
        if app.config.get('PROMETHEUS_METRICS', False):
            # Collect latest system metrics before serving
            if hasattr(app, 'monitor'):
                app.monitor.collect_system_metrics()
            
            return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)
        else:
            return "Metrics disabled", 404

class PerformanceProfiler:
    """Performance profiling utilities"""
    
    def __init__(self):
        self.profiles = {}
    
    def start_profile(self, profile_name):
        """Start a performance profile"""
        self.profiles[profile_name] = {
            'start_time': time.time(),
            'start_memory': psutil.Process().memory_info().rss
        }
    
    def end_profile(self, profile_name):
        """End a performance profile and return metrics"""
        if profile_name not in self.profiles:
            logger.warning(f"Profile {profile_name} not found")
            return None
        
        profile = self.profiles[profile_name]
        end_time = time.time()
        end_memory = psutil.Process().memory_info().rss
        
        metrics = {
            'duration': end_time - profile['start_time'],
            'memory_delta': end_memory - profile['start_memory'],
            'peak_memory': end_memory
        }
        
        # Clean up
        del self.profiles[profile_name]
        
        return metrics
    
    def profile_function(self, func_name):
        """Decorator to profile a function"""
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                self.start_profile(func_name)
                try:
                    result = f(*args, **kwargs)
                    return result
                finally:
                    metrics = self.end_profile(func_name)
                    if metrics and metrics['duration'] > 1.0:
                        logger.info(
                            f"Function {func_name} took {metrics['duration']:.2f}s, "
                            f"memory delta: {metrics['memory_delta'] / 1024 / 1024:.1f}MB"
                        )
            return decorated_function
        return decorator

# Global profiler instance
profiler = PerformanceProfiler()

def init_monitoring(app):
    """Initialize monitoring for the Flask app"""
    monitor = ApplicationMonitor(app)
    app.monitor = monitor
    
    # Create metrics endpoint
    create_metrics_endpoint(app)
    
    return monitor