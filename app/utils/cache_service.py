"""
Caching service for optimizing database queries and expensive operations
"""
from functools import wraps
from flask import current_app
try:
    from app import cache
    # Ensure cache is not None even if import succeeds
    if cache is None:
        import logging
        logging.getLogger(__name__).warning("Cache object is None, caching disabled")
    else:
        import logging
        logging.getLogger(__name__).info(f"Cache object loaded: {type(cache)}")
except ImportError:
    cache = None
    import logging
    logging.getLogger(__name__).warning("Could not import cache from app, caching disabled")
from app.models import User, Property, Task
from sqlalchemy.orm import joinedload, selectinload
import json
import hashlib


def cache_key_generator(*args, **kwargs):
    """Generate a cache key from function arguments"""
    key_data = f"{args}_{kwargs}"
    return hashlib.md5(key_data.encode()).hexdigest()


def cached_query(timeout=300, key_prefix='query'):
    """Decorator for caching database queries"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # If cache is not available, just execute the function
            if cache is None:
                current_app.logger.debug("Cache not available, executing function directly")
                return f(*args, **kwargs)
            
            # Generate cache key
            args_str = '_'.join(str(arg) for arg in args)
            kwargs_str = '_'.join(f"{k}:{v}" for k, v in sorted(kwargs.items()))
            cache_key = f"{key_prefix}_{f.__name__}_{args_str}_{kwargs_str}"
            
            try:
                # Try to get from cache
                result = cache.get(cache_key)
                if result is not None:
                    current_app.logger.debug(f"Cache hit: {cache_key}")
                    return result
                
                # Execute function and cache result
                current_app.logger.debug(f"Cache miss: {cache_key}")
                result = f(*args, **kwargs)
                cache.set(cache_key, result, timeout=timeout)
                return result
            except Exception as cache_error:
                current_app.logger.warning(f"Cache operation failed for {cache_key}: {cache_error}")
                # Fallback to direct execution if cache fails
                return f(*args, **kwargs)
        return decorated_function
    return decorator


class CacheService:
    """Centralized caching service for the application"""
    
    @staticmethod
    @cached_query(timeout=600, key_prefix='user_dashboard')
    def get_user_dashboard_data(user_id):
        """Get optimized user dashboard data with caching"""
        try:
            user = User.query.options(
                joinedload(User.properties).selectinload(Property.rooms),
                selectinload(User.assigned_tasks).joinedload(Task.property),
                selectinload(User.created_tasks)
            ).filter_by(id=user_id).first()
            
            if not user:
                return None
            
            # Convert to serializable format for caching
            return {
                'user': {
                    'id': user.id,
                    'name': user.get_full_name(),
                    'email': user.email,
                    'role': user.role
                },
                'properties': [
                    {
                        'id': prop.id,
                        'name': prop.name,
                        'address': prop.address,
                        'room_count': len(prop.rooms) if prop.rooms else 0
                    } for prop in user.properties
                ],
                'assigned_tasks': [
                    {
                        'id': task.id,
                        'title': task.title,
                        'status': task.status.value if task.status else None,
                        'due_date': task.due_date.isoformat() if task.due_date else None,
                        'property_name': task.property.name if task.property else None
                    } for task in user.assigned_tasks[:10]  # Limit to recent tasks
                ],
                'created_tasks': [
                    {
                        'id': task.id,
                        'title': task.title,
                        'status': task.status.value if task.status else None,
                        'due_date': task.due_date.isoformat() if task.due_date else None
                    } for task in user.created_tasks[:10]  # Limit to recent tasks
                ]
            }
        except Exception as e:
            current_app.logger.error(f"Error getting user dashboard data: {e}")
            return None
    
    @staticmethod
    @cached_query(timeout=1800, key_prefix='property_stats')
    def get_property_statistics(property_id):
        """Get property statistics with caching"""
        try:
            property = Property.query.get(property_id)
            if not property:
                return None
            
            # Calculate statistics
            total_tasks = property.property_tasks.count()
            completed_tasks = property.property_tasks.filter_by(status='completed').count()
            pending_tasks = property.property_tasks.filter_by(status='pending').count()
            
            return {
                'property_id': property_id,
                'total_tasks': total_tasks,
                'completed_tasks': completed_tasks,
                'pending_tasks': pending_tasks,
                'completion_rate': (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0,
                'room_count': len(property.rooms) if property.rooms else 0
            }
        except Exception as e:
            current_app.logger.error(f"Error getting property statistics: {e}")
            return None
    
    @staticmethod
    @cached_query(timeout=900, key_prefix='task_summary')
    def get_user_task_summary(user_id):
        """Get user task summary with caching"""
        try:
            from app.models import TaskStatus
            from datetime import datetime, timedelta
            
            today = datetime.utcnow().date()
            week_ago = today - timedelta(days=7)
            
            # Count tasks by status
            pending_count = Task.query.filter_by(
                creator_id=user_id, 
                status=TaskStatus.PENDING
            ).count()
            
            in_progress_count = Task.query.filter_by(
                creator_id=user_id, 
                status=TaskStatus.IN_PROGRESS
            ).count()
            
            completed_today = Task.query.filter(
                Task.creator_id == user_id,
                Task.status == TaskStatus.COMPLETED,
                Task.completed_at >= today
            ).count()
            
            completed_week = Task.query.filter(
                Task.creator_id == user_id,
                Task.status == TaskStatus.COMPLETED,
                Task.completed_at >= week_ago
            ).count()
            
            return {
                'pending': pending_count,
                'in_progress': in_progress_count,
                'completed_today': completed_today,
                'completed_week': completed_week,
                'total_active': pending_count + in_progress_count
            }
        except Exception as e:
            current_app.logger.error(f"Error getting task summary: {e}")
            return {
                'pending': 0,
                'in_progress': 0,
                'completed_today': 0,
                'completed_week': 0,
                'total_active': 0
            }
    
    @staticmethod
    @cached_query(timeout=3600, key_prefix='system_stats')
    def get_system_statistics():
        """Get system-wide statistics with caching"""
        try:
            total_users = User.query.count()
            total_properties = Property.query.count()
            total_tasks = Task.query.count()
            active_users = User.query.filter_by(is_active=True).count()
            
            return {
                'total_users': total_users,
                'active_users': active_users,
                'total_properties': total_properties,
                'total_tasks': total_tasks,
                'user_activity_rate': (active_users / total_users * 100) if total_users > 0 else 0
            }
        except Exception as e:
            current_app.logger.error(f"Error getting system statistics: {e}")
            return {
                'total_users': 0,
                'active_users': 0,
                'total_properties': 0,
                'total_tasks': 0,
                'user_activity_rate': 0
            }
    
    @staticmethod
    def invalidate_user_cache(user_id):
        """Invalidate all cache entries for a specific user"""
        if cache is None:
            return
            
        cache_patterns = [
            f"user_dashboard_get_user_dashboard_data_{user_id}",
            f"task_summary_get_user_task_summary_{user_id}"
        ]
        
        for pattern in cache_patterns:
            try:
                cache.delete(pattern)
            except Exception as e:
                current_app.logger.warning(f"Failed to delete cache pattern {pattern}: {e}")
        
        # Also invalidate system stats as they include user counts
        try:
            cache.delete_many("system_stats_*")
        except Exception as e:
            current_app.logger.warning(f"Failed to delete system stats cache: {e}")
        current_app.logger.debug(f"Invalidated cache for user {user_id}")
    
    @staticmethod
    def invalidate_property_cache(property_id):
        """Invalidate all cache entries for a specific property"""
        if cache is None:
            return
            
        cache_patterns = [
            f"property_stats_get_property_statistics_{property_id}"
        ]
        
        for pattern in cache_patterns:
            try:
                cache.delete(pattern)
            except Exception as e:
                current_app.logger.warning(f"Failed to delete cache pattern {pattern}: {e}")
        
        current_app.logger.debug(f"Invalidated cache for property {property_id}")
    
    @staticmethod
    def invalidate_task_cache(user_id=None):
        """Invalidate task-related cache entries"""
        if cache is None:
            return
            
        if user_id:
            cache_patterns = [
                f"task_summary_get_user_task_summary_{user_id}",
                f"user_dashboard_get_user_dashboard_data_{user_id}"
            ]
            
            for pattern in cache_patterns:
                try:
                    cache.delete(pattern)
                except Exception as e:
                    current_app.logger.warning(f"Failed to delete cache pattern {pattern}: {e}")
        else:
            # Invalidate all task-related caches
            try:
                cache.delete_many("task_summary_*")
                cache.delete_many("user_dashboard_*")
            except Exception as e:
                current_app.logger.warning(f"Failed to delete task-related caches: {e}")
        
        current_app.logger.debug(f"Invalidated task cache for user {user_id}")
    
    @staticmethod
    def warm_cache(user_id):
        """Pre-populate cache with commonly accessed data for a user"""
        try:
            # Pre-load dashboard data
            CacheService.get_user_dashboard_data(user_id)
            
            # Pre-load task summary
            CacheService.get_user_task_summary(user_id)
            
            # Pre-load property stats for user's properties
            user = User.query.get(user_id)
            if user and user.properties:
                for property in user.properties:
                    CacheService.get_property_statistics(property.id)
            
            current_app.logger.info(f"Cache warmed for user {user_id}")
        except Exception as e:
            current_app.logger.error(f"Error warming cache for user {user_id}: {e}")
    
    @staticmethod
    def get_cache_stats():
        """Get cache performance statistics"""
        try:
            # This would depend on the cache backend
            # For Redis, we could get memory usage, hit rates, etc.
            if current_app.config.get('CACHE_TYPE') == 'redis':
                import redis
                redis_url = current_app.config.get('REDIS_URL')
                if redis_url:
                    r = redis.from_url(redis_url)
                    info = r.info()
                    
                    return {
                        'memory_usage': info.get('used_memory_human', 'unknown'),
                        'keyspace_hits': info.get('keyspace_hits', 0),
                        'keyspace_misses': info.get('keyspace_misses', 0),
                        'connected_clients': info.get('connected_clients', 0),
                        'hit_rate': (info.get('keyspace_hits', 0) / 
                                   (info.get('keyspace_hits', 0) + info.get('keyspace_misses', 1)) * 100)
                    }
            
            return {'message': 'Cache statistics not available for current backend'}
        except Exception as e:
            current_app.logger.error(f"Error getting cache stats: {e}")
            return {'error': str(e)}


# Cache invalidation decorators for models
def invalidate_cache_on_save(cache_service_method):
    """Decorator to invalidate cache when model is saved"""
    def decorator(model_class):
        original_save = getattr(model_class, 'save', None)
        
        def new_save(self, *args, **kwargs):
            result = original_save(self, *args, **kwargs) if original_save else None
            cache_service_method(self.id)
            return result
        
        model_class.save = new_save
        return model_class
    return decorator 