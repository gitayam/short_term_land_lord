"""
Database Query Optimization Utilities

This module provides tools for optimizing database queries, monitoring performance,
and implementing efficient eager loading strategies.
"""

from sqlalchemy.orm import joinedload, selectinload, subqueryload
from sqlalchemy import event, text
from sqlalchemy.engine import Engine
from flask import current_app, g
from flask_login import current_user
import time
import logging
from app.models import User, Property, Task, Room, Booking

logger = logging.getLogger(__name__)

class DatabaseOptimizer:
    """Database query optimization utilities"""
    
    @staticmethod
    def optimize_user_queries():
        """Get optimized query options for user-related queries"""
        return {
            'properties': joinedload(User.properties),
            'tasks': selectinload(User.assigned_tasks),
            'role_assignments': joinedload(User.role_assignments) if hasattr(User, 'role_assignments') else None
        }
    
    @staticmethod
    def optimize_property_queries():
        """Get optimized query options for property-related queries"""
        return {
            'owner': joinedload(Property.owner),
            'rooms': selectinload(Property.rooms),
            'tasks': selectinload(Property.property_tasks),
            'bookings': selectinload(Property.bookings) if hasattr(Property, 'bookings') else None
        }
    
    @staticmethod
    def optimize_task_queries():
        """Get optimized query options for task-related queries"""
        return {
            'property': joinedload(Task.property),
            'creator': joinedload(Task.creator),
            'assignee': joinedload(Task.assignee) if hasattr(Task, 'assignee') else None
        }
    
    @staticmethod
    def get_user_dashboard_data(user_id):
        """Optimized query for user dashboard data"""
        try:
            return User.query.options(
                joinedload(User.properties).selectinload(Property.rooms),
                selectinload(User.assigned_tasks).joinedload(Task.property),
                selectinload(User.created_tasks)
            ).filter_by(id=user_id).first()
        except Exception as e:
            logger.error(f"Error fetching user dashboard data: {e}")
            return User.query.get(user_id)
    
    @staticmethod
    def get_property_with_relations(property_id):
        """Optimized query for property with all related data"""
        try:
            return Property.query.options(
                joinedload(Property.owner),
                selectinload(Property.rooms),
                selectinload(Property.property_tasks).joinedload(Task.assignee) if hasattr(Task, 'assignee') else selectinload(Property.property_tasks),
                selectinload(Property.bookings) if hasattr(Property, 'bookings') else None
            ).filter_by(id=property_id).first()
        except Exception as e:
            logger.error(f"Error fetching property data: {e}")
            return Property.query.get(property_id)
    
    @staticmethod
    def get_user_tasks_optimized(user_id, status=None):
        """Optimized query for user tasks with property information"""
        try:
            query = Task.query.options(
                joinedload(Task.property),
                joinedload(Task.creator)
            ).filter_by(assignee_id=user_id)
            
            if status:
                query = query.filter_by(status=status)
            
            return query.all()
        except Exception as e:
            logger.error(f"Error fetching user tasks: {e}")
            return []

class QueryPerformanceMonitor:
    """Monitor and log database query performance"""
    
    def __init__(self):
        self.slow_query_threshold = 0.1  # 100ms
        self.setup_monitoring()
    
    def setup_monitoring(self):
        """Set up SQLAlchemy event listeners for query monitoring"""
        @event.listens_for(Engine, "before_cursor_execute")
        def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            context._query_start_time = time.time()
            context._query_statement = statement
        
        @event.listens_for(Engine, "after_cursor_execute")
        def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            total = time.time() - context._query_start_time
            
            # Log slow queries
            if total > self.slow_query_threshold:
                logger.warning(
                    f"Slow query detected: {total:.3f}s - {statement[:200]}..."
                )
                
                # Add to request context for monitoring
                if hasattr(g, 'slow_queries'):
                    g.slow_queries.append({
                        'duration': total,
                        'statement': statement[:200],
                        'timestamp': time.time()
                    })
                else:
                    g.slow_queries = [{
                        'duration': total,
                        'statement': statement[:200],
                        'timestamp': time.time()
                    }]
    
    @staticmethod
    def get_db_metrics():
        """Collect database performance metrics"""
        metrics = {}
        
        try:
            from app import db
            
            # Connection count for PostgreSQL
            if 'postgresql' in current_app.config.get('SQLALCHEMY_DATABASE_URI', ''):
                result = db.session.execute(text("""
                    SELECT count(*) as active_connections
                    FROM pg_stat_activity
                    WHERE state = 'active'
                """))
                metrics['active_connections'] = result.scalar()
                
                # Database size
                result = db.session.execute(text("""
                    SELECT pg_size_pretty(pg_database_size(current_database())) as db_size
                """))
                metrics['database_size'] = result.scalar()
                
                # Table sizes
                result = db.session.execute(text("""
                    SELECT 
                        schemaname,
                        tablename,
                        pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
                    FROM pg_tables 
                    WHERE schemaname = 'public'
                    ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
                    LIMIT 10
                """))
                metrics['largest_tables'] = [dict(row) for row in result.fetchall()]
            
        except Exception as e:
            logger.error(f"Database monitoring error: {e}")
        
        return metrics

class DatabaseIndexManager:
    """Manage database indexes for optimal performance"""
    
    @staticmethod
    def create_performance_indexes():
        """Create additional indexes for production performance"""
        from app import db
        
        try:
            # Check if we're using PostgreSQL
            if 'postgresql' in current_app.config.get('SQLALCHEMY_DATABASE_URI', ''):
                indexes = [
                    "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_task_status_due_date ON task (status, due_date)",
                    "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_task_property_status ON task (property_id, status)",
                    "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_role_active ON users (role, is_active)",
                    "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_property_owner_status ON property (owner_id, status)",
                    "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_task_assignee_status ON task (assignee_id, status)"
                ]
                
                for index_sql in indexes:
                    try:
                        db.session.execute(text(index_sql))
                        db.session.commit()
                        logger.info(f"Created index: {index_sql}")
                    except Exception as e:
                        db.session.rollback()
                        logger.warning(f"Index creation failed (may already exist): {e}")
                        
        except Exception as e:
            logger.error(f"Error creating performance indexes: {e}")
    
    @staticmethod
    def analyze_missing_indexes():
        """Analyze potentially missing indexes (PostgreSQL only)"""
        from app import db
        
        try:
            if 'postgresql' in current_app.config.get('SQLALCHEMY_DATABASE_URI', ''):
                result = db.session.execute(text("""
                    SELECT 
                        schemaname,
                        tablename,
                        attname,
                        n_distinct,
                        correlation
                    FROM pg_stats
                    WHERE schemaname = 'public'
                    AND n_distinct > 100
                    ORDER BY n_distinct DESC
                    LIMIT 20
                """))
                
                return [dict(row) for row in result.fetchall()]
        except Exception as e:
            logger.error(f"Error analyzing indexes: {e}")
        
        return []

# Initialize global instances
query_monitor = QueryPerformanceMonitor()
db_optimizer = DatabaseOptimizer()
index_manager = DatabaseIndexManager()