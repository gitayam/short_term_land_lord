"""
Cache Management System

This module provides Redis-based caching capabilities with comprehensive
cache management, invalidation strategies, and performance monitoring.
"""

from flask_caching import Cache
from functools import wraps
import pickle
import json
import hashlib
import time
import logging
from datetime import datetime, timedelta
from flask import current_app

logger = logging.getLogger(__name__)

# Global cache instance
cache = Cache()

def cache_key(*args, **kwargs):
    """Generate cache key from function arguments"""
    key_data = f"{args}_{kwargs}"
    return hashlib.md5(key_data.encode()).hexdigest()

def cached_query(timeout=300, key_prefix='query'):
    """Decorator for caching database queries"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Generate cache key
            func_name = f.__name__
            args_hash = hashlib.md5(str(args).encode() + str(kwargs).encode()).hexdigest()
            cache_key = f"{key_prefix}_{func_name}_{args_hash}"
            
            # Try to get from cache
            result = cache.get(cache_key)
            
            if result is None:
                try:
                    result = f(*args, **kwargs)
                    cache.set(cache_key, result, timeout=timeout)
                    logger.debug(f"Cache miss - stored result for key: {cache_key}")
                except Exception as e:
                    logger.error(f"Error executing cached function {func_name}: {e}")
                    result = None
            else:
                logger.debug(f"Cache hit for key: {cache_key}")
            
            return result
        return decorated_function
    return decorator

class CacheService:
    """Service class for managing application caching"""
    
    @staticmethod
    @cached_query(timeout=600, key_prefix='user_dashboard')
    def get_user_dashboard_data(user_id):
        """Cached user dashboard data"""
        try:
            from app.utils.db_optimizer import DatabaseOptimizer
            return DatabaseOptimizer.get_user_dashboard_data(user_id)
        except Exception as e:
            logger.error(f"Error fetching user dashboard data: {e}")
            return None
    
    @staticmethod
    @cached_query(timeout=3600, key_prefix='property_stats')
    def get_property_statistics(property_id):
        """Cached property statistics"""
        try:
            from app.models import Property, Task
            
            property = Property.query.get(property_id)
            if not property:
                return None
            
            # Calculate statistics
            stats = {
                'total_tasks': property.property_tasks.count() if hasattr(property, 'property_tasks') else 0,
                'completed_tasks': property.property_tasks.filter_by(status='completed').count() if hasattr(property, 'property_tasks') else 0,
                'pending_tasks': property.property_tasks.filter_by(status='pending').count() if hasattr(property, 'property_tasks') else 0,
                'room_count': len(property.rooms) if property.rooms else 0,
                'last_updated': datetime.utcnow().isoformat()
            }
            
            return stats
        except Exception as e:
            logger.error(f"Error calculating property statistics: {e}")
            return None
    
    @staticmethod
    @cached_query(timeout=1800, key_prefix='task_summary')
    def get_task_summary(user_id):
        """Cached task summary for user"""
        try:
            from app.models import Task
            
            today = datetime.utcnow().date()
            
            summary = {
                'pending': Task.query.filter_by(assignee_id=user_id, status='pending').count(),
                'in_progress': Task.query.filter_by(assignee_id=user_id, status='in_progress').count(),
                'completed_today': Task.query.filter(
                    Task.assignee_id == user_id,
                    Task.status == 'completed',
                    Task.updated_at >= today
                ).count() if hasattr(Task, 'updated_at') else 0,
                'overdue': Task.query.filter(
                    Task.assignee_id == user_id,
                    Task.status.in_(['pending', 'in_progress']),
                    Task.due_date < datetime.utcnow()
                ).count() if hasattr(Task, 'due_date') else 0
            }
            
            return summary
        except Exception as e:
            logger.error(f"Error generating task summary: {e}")
            return {}
    
    @staticmethod
    @cached_query(timeout=7200, key_prefix='system_stats')
    def get_system_statistics():
        """Cached system-wide statistics"""
        try:
            from app.models import User, Property, Task
            
            stats = {
                'total_users': User.query.count(),
                'active_users': User.query.filter_by(is_active=True).count() if hasattr(User, 'is_active') else User.query.count(),
                'total_properties': Property.query.count(),
                'total_tasks': Task.query.count(),
                'completed_tasks': Task.query.filter_by(status='completed').count(),
                'last_updated': datetime.utcnow().isoformat()
            }
            
            return stats
        except Exception as e:
            logger.error(f"Error generating system statistics: {e}")
            return {}

class CacheInvalidator:
    """Utility class for cache invalidation strategies"""
    
    @staticmethod
    def invalidate_user_cache(user_id):
        """Invalidate all cache entries for a user"""
        try:
            patterns = [
                f"user_dashboard_*_{user_id}_*",
                f"task_summary_*_{user_id}_*"
            ]
            
            for pattern in patterns:
                CacheInvalidator._delete_pattern(pattern)
            
            logger.info(f"Invalidated cache for user {user_id}")
        except Exception as e:
            logger.error(f"Error invalidating user cache: {e}")
    
    @staticmethod
    def invalidate_property_cache(property_id):
        """Invalidate all cache entries for a property"""
        try:
            patterns = [
                f"property_stats_*_{property_id}_*",
                f"query_*property*{property_id}*"
            ]
            
            for pattern in patterns:
                CacheInvalidator._delete_pattern(pattern)
            
            logger.info(f"Invalidated cache for property {property_id}")
        except Exception as e:
            logger.error(f"Error invalidating property cache: {e}")
    
    @staticmethod
    def invalidate_task_cache(task_id=None, user_id=None, property_id=None):
        """Invalidate task-related cache entries"""
        try:
            patterns = ["task_summary_*", "query_*task*"]
            
            if user_id:
                patterns.append(f"user_dashboard_*_{user_id}_*")
            
            if property_id:
                patterns.append(f"property_stats_*_{property_id}_*")
            
            for pattern in patterns:
                CacheInvalidator._delete_pattern(pattern)
            
            logger.info(f"Invalidated task cache (task_id={task_id}, user_id={user_id}, property_id={property_id})")
        except Exception as e:
            logger.error(f"Error invalidating task cache: {e}")
    
    @staticmethod
    def invalidate_system_cache():
        """Invalidate system-wide cache entries"""
        try:
            patterns = ["system_stats_*"]
            
            for pattern in patterns:
                CacheInvalidator._delete_pattern(pattern)
            
            logger.info("Invalidated system cache")
        except Exception as e:
            logger.error(f"Error invalidating system cache: {e}")
    
    @staticmethod
    def _delete_pattern(pattern):
        """Delete cache keys matching a pattern"""
        try:
            # This is a simplified implementation
            # In production, you might want to use Redis SCAN command for efficiency
            if hasattr(cache.cache, '_write_client'):
                # Redis backend
                redis_client = cache.cache._write_client
                keys = redis_client.keys(pattern)
                if keys:
                    redis_client.delete(*keys)
            else:
                # Simple cache backend - clear all
                cache.clear()
        except Exception as e:
            logger.error(f"Error deleting cache pattern {pattern}: {e}")

class CacheMetrics:
    """Cache performance metrics and monitoring"""
    
    def __init__(self):
        self.hit_count = 0
        self.miss_count = 0
        self.error_count = 0
        self.last_reset = datetime.utcnow()
    
    def record_hit(self):
        """Record cache hit"""
        self.hit_count += 1
    
    def record_miss(self):
        """Record cache miss"""
        self.miss_count += 1
    
    def record_error(self):
        """Record cache error"""
        self.error_count += 1
    
    def get_hit_rate(self):
        """Calculate cache hit rate"""
        total = self.hit_count + self.miss_count
        return (self.hit_count / total * 100) if total > 0 else 0
    
    def get_stats(self):
        """Get cache statistics"""
        return {
            'hit_count': self.hit_count,
            'miss_count': self.miss_count,
            'error_count': self.error_count,
            'hit_rate': self.get_hit_rate(),
            'last_reset': self.last_reset.isoformat()
        }
    
    def reset(self):
        """Reset cache metrics"""
        self.hit_count = 0
        self.miss_count = 0
        self.error_count = 0
        self.last_reset = datetime.utcnow()

# Global cache metrics instance
cache_metrics = CacheMetrics()

def init_cache(app):
    """Initialize cache with Flask app"""
    try:
        cache.init_app(app)
        logger.info("Cache initialized successfully")
        
        # Test cache connectivity
        cache.set('test_key', 'test_value', timeout=10)
        if cache.get('test_key') == 'test_value':
            logger.info("Cache connectivity test passed")
            cache.delete('test_key')
        else:
            logger.warning("Cache connectivity test failed")
            
    except Exception as e:
        logger.error(f"Error initializing cache: {e}")
        # Fallback to simple cache if Redis fails
        app.config['CACHE_TYPE'] = 'simple'
        cache.init_app(app)
        logger.warning("Fallback to simple cache due to Redis connection failure")

def warm_cache():
    """Warm up cache with frequently accessed data"""
    try:
        from app.models import User, Property
        
        # Cache system statistics
        CacheService.get_system_statistics()
        
        # Cache data for active users
        active_users = User.query.filter_by(is_active=True).limit(10).all() if hasattr(User, 'is_active') else User.query.limit(10).all()
        for user in active_users:
            CacheService.get_user_dashboard_data(user.id)
            CacheService.get_task_summary(user.id)
        
        # Cache data for recent properties
        recent_properties = Property.query.order_by(Property.id.desc()).limit(10).all()
        for property in recent_properties:
            CacheService.get_property_statistics(property.id)
        
        logger.info("Cache warmed successfully")
    except Exception as e:
        logger.error(f"Error warming cache: {e}")