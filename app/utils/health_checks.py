"""
Health check system for production monitoring
"""
import time
import psutil
from flask import current_app
from sqlalchemy import text
from app.models import db
from app import cache
import redis


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
        if current_app.config.get('CACHE_TYPE') != 'redis':
            return {
                'status': 'not_configured',
                'message': 'Redis caching not configured'
            }
        
        try:
            start_time = time.time()
            
            # Test basic connectivity
            cache.set('health_check', 'ok', timeout=10)
            result = cache.get('health_check')
            response_time = time.time() - start_time
            
            if result != 'ok':
                return {
                    'status': 'unhealthy',
                    'message': 'Redis not responding correctly'
                }
            
            # Get Redis info
            try:
                redis_url = current_app.config.get('REDIS_URL')
                if redis_url:
                    r = redis.from_url(redis_url)
                    info = r.info()
                    memory_usage = info.get('used_memory_human', 'unknown')
                    connected_clients = info.get('connected_clients', 'unknown')
                    
                    redis_info = {
                        'memory_usage': memory_usage,
                        'connected_clients': connected_clients,
                        'version': info.get('redis_version', 'unknown')
                    }
                else:
                    redis_info = {}
            except:
                redis_info = {}
            
            if response_time > 0.1:
                return {
                    'status': 'warning',
                    'message': f'Redis slow: {response_time:.2f}s',
                    'response_time': response_time,
                    'redis_info': redis_info
                }
            
            return {
                'status': 'healthy',
                'message': 'Redis connected',
                'response_time': response_time,
                'redis_info': redis_info
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'message': f'Redis error: {str(e)}'
            }
    
    def check_memory(self):
        """Check system memory usage"""
        try:
            memory = psutil.virtual_memory()
            used_percent = memory.percent
            available_mb = memory.available / (1024 * 1024)
            
            memory_info = {
                'used_percent': used_percent,
                'available_mb': round(available_mb, 2),
                'total_mb': round(memory.total / (1024 * 1024), 2)
            }
            
            if used_percent > 95:
                return {
                    'status': 'unhealthy',
                    'message': f'Critical memory usage: {used_percent:.1f}%',
                    'memory_info': memory_info
                }
            elif used_percent > 85:
                return {
                    'status': 'warning',
                    'message': f'High memory usage: {used_percent:.1f}%',
                    'memory_info': memory_info
                }
            
            return {
                'status': 'healthy',
                'message': f'Memory usage OK: {used_percent:.1f}%',
                'memory_info': memory_info
            }
            
        except Exception as e:
            return {
                'status': 'unknown',
                'message': f'Cannot check memory: {str(e)}'
            }
    
    def check_disk_space(self):
        """Check disk space usage"""
        try:
            import shutil
            total, used, free = shutil.disk_usage('/')
            free_percent = (free / total) * 100
            
            disk_info = {
                'free_percent': round(free_percent, 2),
                'free_gb': round(free / (1024**3), 2),
                'total_gb': round(total / (1024**3), 2),
                'used_gb': round(used / (1024**3), 2)
            }
            
            if free_percent < 5:
                return {
                    'status': 'unhealthy',
                    'message': f'Critical disk space: {free_percent:.1f}% free',
                    'disk_info': disk_info
                }
            elif free_percent < 15:
                return {
                    'status': 'warning',
                    'message': f'Low disk space: {free_percent:.1f}% free',
                    'disk_info': disk_info
                }
            
            return {
                'status': 'healthy',
                'message': f'Disk space OK: {free_percent:.1f}% free',
                'disk_info': disk_info
            }
            
        except Exception as e:
            return {
                'status': 'unknown',
                'message': f'Cannot check disk space: {str(e)}'
            }
    
    def check_external_services(self):
        """Check external service configuration"""
        services = {}
        
        # Check Twilio
        if current_app.config.get('TWILIO_ACCOUNT_SID'):
            services['twilio'] = {
                'status': 'configured',
                'message': 'Twilio SMS service configured'
            }
        else:
            services['twilio'] = {
                'status': 'not_configured',
                'message': 'Twilio SMS service not configured'
            }
        
        # Check Email
        if current_app.config.get('MAIL_SERVER'):
            services['email'] = {
                'status': 'configured',
                'message': 'Email service configured'
            }
        else:
            services['email'] = {
                'status': 'not_configured',
                'message': 'Email service not configured'
            }
        
        # Check S3
        if current_app.config.get('S3_BUCKET'):
            services['s3'] = {
                'status': 'configured',
                'message': 'S3 storage configured'
            }
        else:
            services['s3'] = {
                'status': 'not_configured',
                'message': 'S3 storage not configured'
            }
        
        # Check Sentry
        if current_app.config.get('SENTRY_DSN'):
            services['sentry'] = {
                'status': 'configured',
                'message': 'Sentry error tracking configured'
            }
        else:
            services['sentry'] = {
                'status': 'not_configured',
                'message': 'Sentry error tracking not configured'
            }
        
        # Determine overall status
        configured_count = sum(1 for s in services.values() if s['status'] == 'configured')
        total_count = len(services)
        
        return {
            'status': 'healthy',
            'message': f'{configured_count}/{total_count} external services configured',
            'services': services
        }
    
    def run_all_checks(self):
        """Run all health checks and return summary"""
        results = {}
        overall_status = 'healthy'
        start_time = time.time()
        
        for check_name, check_func in self.checks.items():
            try:
                result = check_func()
                results[check_name] = result
                
                # Determine overall status
                if result.get('status') == 'unhealthy':
                    overall_status = 'unhealthy'
                elif result.get('status') == 'warning' and overall_status != 'unhealthy':
                    overall_status = 'warning'
                    
            except Exception as e:
                results[check_name] = {
                    'status': 'error',
                    'message': f'Health check failed: {str(e)}'
                }
                overall_status = 'unhealthy'
        
        total_time = time.time() - start_time
        
        return {
            'status': overall_status,
            'timestamp': time.time(),
            'total_check_time': round(total_time, 3),
            'checks': results,
            'summary': {
                'healthy': sum(1 for r in results.values() if r.get('status') == 'healthy'),
                'warning': sum(1 for r in results.values() if r.get('status') == 'warning'),
                'unhealthy': sum(1 for r in results.values() if r.get('status') == 'unhealthy'),
                'error': sum(1 for r in results.values() if r.get('status') == 'error'),
                'not_configured': sum(1 for r in results.values() if r.get('status') == 'not_configured')
            }
        }


class QuickHealthChecker:
    """Lightweight health checker for frequent checks"""
    
    @staticmethod
    def quick_check():
        """Quick health check - only essential services"""
        try:
            # Quick database check
            db.session.execute(text('SELECT 1'))
            
            # Quick cache check if Redis enabled
            if current_app.config.get('CACHE_TYPE') == 'redis':
                cache.set('quick_health', 'ok', timeout=5)
                cache_result = cache.get('quick_health')
                if cache_result != 'ok':
                    raise Exception("Cache not responding")
            
            return {
                'status': 'healthy',
                'message': 'All essential services operational',
                'timestamp': time.time()
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'message': f'Essential service failure: {str(e)}',
                'timestamp': time.time()
            } 