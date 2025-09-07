"""
Health check system for production monitoring
"""
import time
import psutil
from flask import current_app
from sqlalchemy import text
from app.models import db
from app import cache
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    redis = None
    REDIS_AVAILABLE = False


class HealthChecker:
    """Comprehensive health check system"""
    
    def __init__(self):
        self.checks = {
            'database': self.check_database,
            'redis': self.check_redis,
            'memory': self.check_memory,
            'disk_space': self.check_disk_space,
            'external_services': self.check_external_services
        }
    
    def check_database(self):
        """Check database connectivity and performance"""
        try:
            start_time = time.time()
            
            # Test basic connectivity
            result = db.session.execute(text('SELECT 1'))
            response_time = time.time() - start_time
            
            # Check connection pool status
            pool_info = {}
            if hasattr(db.engine.pool, 'size'):
                pool_info = {
                    'pool_size': db.engine.pool.size(),
                    'checked_in': db.engine.pool.checkedin(),
                    'checked_out': db.engine.pool.checkedout(),
                    'overflow': db.engine.pool.overflow(),
                }
            
            # Performance thresholds
            if response_time > 1.0:
                return {
                    'status': 'warning',
                    'message': f'Database slow: {response_time:.2f}s',
                    'response_time': response_time,
                    'pool_info': pool_info
                }
            elif response_time > 2.0:
                return {
                    'status': 'unhealthy',
                    'message': f'Database very slow: {response_time:.2f}s',
                    'response_time': response_time,
                    'pool_info': pool_info
                }
            
            return {
                'status': 'healthy',
                'message': 'Database connected',
                'response_time': response_time,
                'pool_info': pool_info
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'message': f'Database error: {str(e)}'
            }
    
    def check_redis(self):
        """Check Redis connectivity and performance"""
        if not REDIS_AVAILABLE:
            return {
                "status": "skipped",
                "message": "Redis not available",
                "response_time": 0
            }
        
        if not cache or not hasattr(cache, "cache"):
            return {
                "status": "skipped", 
                "message": "Cache not configured",
                "response_time": 0
            }
        
        try:
            start_time = time.time()
            # Test Redis connection
            cache.set("health_check", "ok", timeout=1)
            result = cache.get("health_check")
            response_time = time.time() - start_time
            
            if result == "ok":
                return {
                    "status": "healthy",
                    "response_time": response_time,
                    "message": "Redis responding normally"
                }
            else:
                return {
                    "status": "error",
                    "response_time": response_time,
                    "error": "Redis test failed"
                }
        except Exception as e:
            return {
                "status": "error",
                "response_time": time.time() - start_time if "start_time" in locals() else 0,
                "error": str(e)
            }        
}
