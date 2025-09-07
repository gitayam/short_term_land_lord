"""
Performance optimization utilities
"""
import time
import functools
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Callable
from flask import current_app, g
from sqlalchemy.orm import joinedload, selectinload, subqueryload


class Timer:
    """Context manager for timing operations"""
    
    def __init__(self, operation_name: str = None):
        self.operation_name = operation_name
        self.start_time = None
        self.end_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        duration = self.duration_ms
        
        if self.operation_name:
            current_app.logger.info(f"Timer [{self.operation_name}]: {duration:.2f}ms")
    
    @property
    def duration_ms(self) -> float:
        """Get duration in milliseconds"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time) * 1000
        return 0


def timed_operation(operation_name: str = None):
    """Decorator to time function execution"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            name = operation_name or f"{func.__module__}.{func.__name__}"
            with Timer(name):
                return func(*args, **kwargs)
        return wrapper
    return decorator


class QueryOptimizer:
    """Query optimization utilities"""
    
    @staticmethod
    def optimize_user_query(query):
        """Optimize User model queries"""
        return query.options(
            joinedload('properties'),
            selectinload('assigned_tasks'),
            selectinload('created_tasks')
        )
    
    @staticmethod
    def optimize_property_query(query):
        """Optimize Property model queries"""
        return query.options(
            joinedload('owner'),
            selectinload('property_tasks'),
            selectinload('images'),
            selectinload('rooms')
        )
    
    @staticmethod
    def optimize_task_query(query):
        """Optimize Task model queries"""
        return query.options(
            joinedload('creator'),
            selectinload('assignments'),
            selectinload('task_properties')
        )
    
    @staticmethod
    def get_active_tasks_optimized():
        """Get active tasks with optimized loading"""
        from app.models import Task, TaskStatus
        return QueryOptimizer.optimize_task_query(
            Task.query.filter(
                Task.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS])
            )
        )
    
    @staticmethod
    def get_user_properties_optimized(user_id: int):
        """Get user properties with optimized loading"""
        from app.models import Property
        return QueryOptimizer.optimize_property_query(
            Property.query.filter_by(owner_id=user_id)
        )


class CacheManager:
    """Simple in-memory cache manager"""
    
    def __init__(self):
        self._cache = {}
        self._expiry = {}
    
    def get(self, key: str) -> Any:
        """Get cached value"""
        if key in self._cache:
            if key in self._expiry and datetime.utcnow() > self._expiry[key]:
                self.delete(key)
                return None
            return self._cache[key]
        return None
    
    def set(self, key: str, value: Any, ttl_seconds: int = 300):
        """Set cached value with TTL"""
        self._cache[key] = value
        if ttl_seconds > 0:
            self._expiry[key] = datetime.utcnow() + timedelta(seconds=ttl_seconds)
    
    def delete(self, key: str):
        """Delete cached value"""
        self._cache.pop(key, None)
        self._expiry.pop(key, None)
    
    def clear(self):
        """Clear all cached values"""
        self._cache.clear()
        self._expiry.clear()
    
    def cleanup_expired(self):
        """Remove expired entries"""
        now = datetime.utcnow()
        expired_keys = [
            key for key, expiry in self._expiry.items()
            if expiry < now
        ]
        for key in expired_keys:
            self.delete(key)


# Global cache instance
cache = CacheManager()


def cached(ttl_seconds: int = 300, key_func: Optional[Callable] = None):
    """Decorator for caching function results"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = f"{func.__module__}.{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # Try to get from cache
            result = cache.get(cache_key)
            if result is not None:
                return result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl_seconds)
            return result
        return wrapper
    return decorator


class DatabaseOptimizer:
    """Database optimization utilities"""
    
    @staticmethod
    def analyze_slow_queries():
        """Analyze and log slow queries (PostgreSQL specific)"""
        from app import db
        from sqlalchemy import text
        
        try:
            # Get slow queries from PostgreSQL
            result = db.session.execute(text("""
                SELECT query, mean_time, calls, total_time
                FROM pg_stat_statements 
                WHERE mean_time > 100  -- queries taking more than 100ms on average
                ORDER BY mean_time DESC 
                LIMIT 10
            """))
            
            slow_queries = result.fetchall()
            if slow_queries:
                current_app.logger.warning("Slow queries detected:")
                for query in slow_queries:
                    current_app.logger.warning(
                        f"Query: {query.query[:100]}... "
                        f"Avg: {query.mean_time:.2f}ms "
                        f"Calls: {query.calls} "
                        f"Total: {query.total_time:.2f}ms"
                    )
        except Exception as e:
            # Ignore if pg_stat_statements is not available
            current_app.logger.debug(f"Could not analyze slow queries: {e}")
    
    @staticmethod
    def get_table_sizes():
        """Get table sizes for monitoring"""
        from app import db
        from sqlalchemy import text
        
        try:
            result = db.session.execute(text("""
                SELECT 
                    schemaname,
                    tablename,
                    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
                    pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
                FROM pg_tables 
                WHERE schemaname = 'public'
                ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
            """))
            
            tables = result.fetchall()
            total_size = sum(table.size_bytes for table in tables)
            
            current_app.logger.info(f"Database size analysis - Total: {total_size / (1024*1024):.2f}MB")
            for table in tables[:5]:  # Top 5 largest tables
                current_app.logger.info(f"Table {table.tablename}: {table.size}")
                
        except Exception as e:
            current_app.logger.debug(f"Could not analyze table sizes: {e}")
    
    @staticmethod
    def optimize_indexes():
        """Suggest index optimizations"""
        from app import db
        from sqlalchemy import text
        
        try:
            # Find unused indexes
            result = db.session.execute(text("""
                SELECT 
                    schemaname, 
                    tablename, 
                    indexname, 
                    idx_tup_read, 
                    idx_tup_fetch
                FROM pg_stat_user_indexes 
                WHERE idx_tup_read = 0 AND idx_tup_fetch = 0
                ORDER BY schemaname, tablename
            """))
            
            unused_indexes = result.fetchall()
            if unused_indexes:
                current_app.logger.info("Unused indexes found:")
                for idx in unused_indexes:
                    current_app.logger.info(f"Unused index: {idx.indexname} on {idx.tablename}")
                    
        except Exception as e:
            current_app.logger.debug(f"Could not analyze indexes: {e}")


class RequestProfiler:
    """Profile request performance"""
    
    def __init__(self):
        self.start_time = None
        self.queries = []
    
    def start(self):
        """Start profiling"""
        self.start_time = time.time()
        g.query_count = 0
        g.query_time = 0
    
    def end(self):
        """End profiling and log results"""
        if self.start_time:
            total_time = (time.time() - self.start_time) * 1000
            query_count = getattr(g, 'query_count', 0)
            query_time = getattr(g, 'query_time', 0) * 1000
            
            current_app.logger.info(
                f"Request performance - Total: {total_time:.2f}ms, "
                f"Queries: {query_count}, Query time: {query_time:.2f}ms"
            )
            
            # Log slow requests
            if total_time > 1000:  # Requests taking more than 1 second
                current_app.logger.warning(f"Slow request detected: {total_time:.2f}ms")


def profile_request(f):
    """Decorator to profile request performance"""
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        profiler = RequestProfiler()
        profiler.start()
        try:
            return f(*args, **kwargs)
        finally:
            profiler.end()
    return wrapper


def batch_process(items, batch_size: int = 100, process_func: Callable = None):
    """Process items in batches for better performance"""
    if not process_func:
        raise ValueError("process_func is required")
    
    results = []
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        batch_results = process_func(batch)
        if batch_results:
            results.extend(batch_results)
    
    return results


class MemoryProfiler:
    """Simple memory usage profiler"""
    
    @staticmethod
    def get_memory_usage():
        """Get current memory usage"""
        try:
            import psutil
            import os
            
            process = psutil.Process(os.getpid())
            memory_info = process.memory_info()
            
            return {
                'rss': memory_info.rss / (1024 * 1024),  # MB
                'vms': memory_info.vms / (1024 * 1024),  # MB
                'percent': process.memory_percent()
            }
        except ImportError:
            return None
    
    @staticmethod
    def log_memory_usage(operation: str = ""):
        """Log current memory usage"""
        memory = MemoryProfiler.get_memory_usage()
        if memory:
            current_app.logger.info(
                f"Memory usage {operation}: "
                f"RSS={memory['rss']:.1f}MB, "
                f"VMS={memory['vms']:.1f}MB, "
                f"Percent={memory['percent']:.1f}%"
            )


def optimize_image_upload(image_path: str, max_size: tuple = (1200, 1200), quality: int = 85):
    """Optimize uploaded images for performance"""
    try:
        from PIL import Image
        
        with Image.open(image_path) as img:
            # Convert to RGB if necessary
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            
            # Resize if too large
            if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Save with optimization
            img.save(image_path, 'JPEG', quality=quality, optimize=True)
            
        return True
    except Exception as e:
        current_app.logger.error(f"Image optimization failed: {e}")
        return False