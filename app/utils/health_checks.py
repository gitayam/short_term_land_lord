"""
Comprehensive Health Check System

This module provides health checks for all critical system components including
database, cache, external services, system resources, and application health.
"""

import time
import psutil
import logging
from datetime import datetime, timedelta
from flask import jsonify, current_app
from sqlalchemy import text
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import socket

logger = logging.getLogger(__name__)

class HealthChecker:
    """Comprehensive health check manager"""
    
    def __init__(self):
        self.checks = {
            'database': self.check_database,
            'cache': self.check_cache,
            'disk_space': self.check_disk_space,
            'memory': self.check_memory,
            'cpu': self.check_cpu,
            'external_services': self.check_external_services,
            'application': self.check_application_health
        }
        self.timeout = 30  # Default timeout for all checks
    
    def check_database(self):
        """Check database connectivity and performance"""
        try:
            from app import db
            
            start_time = time.time()
            
            # Test basic connectivity
            result = db.session.execute(text('SELECT 1 as test'))
            connectivity_time = time.time() - start_time
            
            test_value = result.scalar()
            if test_value != 1:
                return {
                    'status': 'unhealthy',
                    'message': 'Database query returned unexpected result',
                    'details': {'expected': 1, 'actual': test_value}
                }
            
            # Test performance
            performance_status = 'healthy'
            performance_message = 'Database responding normally'
            
            if connectivity_time > 1.0:
                performance_status = 'degraded'
                performance_message = f'Database slow: {connectivity_time:.2f}s response time'
            elif connectivity_time > 2.0:
                performance_status = 'unhealthy'
                performance_message = f'Database very slow: {connectivity_time:.2f}s response time'
            
            # Additional database checks for PostgreSQL
            details = {'response_time': connectivity_time}
            
            try:
                if 'postgresql' in current_app.config.get('SQLALCHEMY_DATABASE_URI', ''):
                    # Check connection count
                    conn_result = db.session.execute(text("""
                        SELECT count(*) as active_connections
                        FROM pg_stat_activity
                        WHERE state = 'active'
                    """))
                    active_connections = conn_result.scalar()
                    details['active_connections'] = active_connections
                    
                    # Check database size
                    size_result = db.session.execute(text("""
                        SELECT pg_size_pretty(pg_database_size(current_database())) as db_size
                    """))
                    db_size = size_result.scalar()
                    details['database_size'] = db_size
                    
                    # Warn if too many connections
                    max_connections = int(current_app.config.get('DB_POOL_SIZE', 10)) + int(current_app.config.get('DB_MAX_OVERFLOW', 20))
                    if active_connections > max_connections * 0.8:
                        performance_status = 'degraded'
                        performance_message = f'High connection count: {active_connections}/{max_connections}'
                        
            except Exception as e:
                logger.warning(f"Could not get additional database metrics: {e}")
            
            return {
                'status': performance_status,
                'message': performance_message,
                'details': details
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'message': f'Database connection failed: {str(e)}',
                'details': {'error': str(e)}
            }
    
    def check_cache(self):
        """Check Redis cache connectivity and performance"""
        try:
            # Try to import cache
            from app.utils.cache_manager import cache
            
            start_time = time.time()
            
            # Test basic connectivity
            test_key = f'health_check_{int(time.time())}'
            test_value = 'health_check_value'
            
            # Set a test value
            cache.set(test_key, test_value, timeout=10)
            
            # Get the test value
            retrieved_value = cache.get(test_key)
            
            response_time = time.time() - start_time
            
            # Clean up
            cache.delete(test_key)
            
            if retrieved_value != test_value:
                return {
                    'status': 'unhealthy',
                    'message': 'Cache not responding correctly',
                    'details': {
                        'expected': test_value,
                        'actual': retrieved_value,
                        'response_time': response_time
                    }
                }
            
            # Check performance
            status = 'healthy'
            message = 'Cache responding normally'
            
            if response_time > 0.1:
                status = 'degraded'
                message = f'Cache slow: {response_time:.3f}s response time'
            elif response_time > 0.5:
                status = 'unhealthy'
                message = f'Cache very slow: {response_time:.3f}s response time'
            
            return {
                'status': status,
                'message': message,
                'details': {'response_time': response_time}
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'message': f'Cache connection failed: {str(e)}',
                'details': {'error': str(e)}
            }
    
    def check_disk_space(self):
        """Check disk space availability"""
        try:
            # Check root partition
            disk_usage = psutil.disk_usage('/')
            free_percent = (disk_usage.free / disk_usage.total) * 100
            
            status = 'healthy'
            message = f'Disk space OK: {free_percent:.1f}% free'
            
            if free_percent < 10:
                status = 'unhealthy'
                message = f'Critical disk space: {free_percent:.1f}% free'
            elif free_percent < 20:
                status = 'degraded'
                message = f'Low disk space: {free_percent:.1f}% free'
            
            details = {
                'free_percent': free_percent,
                'free_bytes': disk_usage.free,
                'total_bytes': disk_usage.total,
                'used_bytes': disk_usage.used
            }
            
            # Check upload directory if configured
            upload_path = current_app.config.get('LOCAL_STORAGE_PATH')
            if upload_path:
                try:
                    upload_usage = psutil.disk_usage(upload_path)
                    upload_free_percent = (upload_usage.free / upload_usage.total) * 100
                    details['upload_disk_free_percent'] = upload_free_percent
                    
                    if upload_free_percent < free_percent:
                        status = max(status, 'degraded')
                        message += f', Upload disk: {upload_free_percent:.1f}% free'
                        
                except Exception as e:
                    details['upload_disk_error'] = str(e)
            
            return {
                'status': status,
                'message': message,
                'details': details
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'message': f'Cannot check disk space: {str(e)}',
                'details': {'error': str(e)}
            }
    
    def check_memory(self):
        """Check memory usage"""
        try:
            memory = psutil.virtual_memory()
            used_percent = memory.percent
            
            status = 'healthy'
            message = f'Memory usage OK: {used_percent:.1f}%'
            
            if used_percent > 90:
                status = 'unhealthy'
                message = f'Critical memory usage: {used_percent:.1f}%'
            elif used_percent > 80:
                status = 'degraded'
                message = f'High memory usage: {used_percent:.1f}%'
            
            # Check swap usage
            swap = psutil.swap_memory()
            swap_percent = swap.percent
            
            if swap_percent > 50:
                status = max(status, 'degraded')
                message += f', High swap usage: {swap_percent:.1f}%'
            
            return {
                'status': status,
                'message': message,
                'details': {
                    'memory_used_percent': used_percent,
                    'memory_available_bytes': memory.available,
                    'memory_total_bytes': memory.total,
                    'swap_used_percent': swap_percent,
                    'swap_total_bytes': swap.total
                }
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'message': f'Cannot check memory: {str(e)}',
                'details': {'error': str(e)}
            }
    
    def check_cpu(self):
        """Check CPU usage"""
        try:
            # Get CPU usage over 1 second interval
            cpu_percent = psutil.cpu_percent(interval=1)
            
            status = 'healthy'
            message = f'CPU usage OK: {cpu_percent:.1f}%'
            
            if cpu_percent > 90:
                status = 'unhealthy'
                message = f'Critical CPU usage: {cpu_percent:.1f}%'
            elif cpu_percent > 80:
                status = 'degraded'
                message = f'High CPU usage: {cpu_percent:.1f}%'
            
            # Get load average (Unix systems)
            details = {'cpu_percent': cpu_percent}
            
            try:
                load_avg = psutil.getloadavg()
                details.update({
                    'load_1min': load_avg[0],
                    'load_5min': load_avg[1],
                    'load_15min': load_avg[2]
                })
                
                # Check if load is high relative to CPU count
                cpu_count = psutil.cpu_count()
                if load_avg[0] > cpu_count * 2:
                    status = max(status, 'degraded')
                    message += f', High load: {load_avg[0]:.1f}'
                    
            except AttributeError:
                # getloadavg not available on Windows
                pass
            
            return {
                'status': status,
                'message': message,
                'details': details
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'message': f'Cannot check CPU: {str(e)}',
                'details': {'error': str(e)}
            }
    
    def check_external_services(self):
        """Check external service connectivity"""
        services = {
            'twilio': {
                'url': 'https://api.twilio.com',
                'config_key': 'TWILIO_ACCOUNT_SID'
            },
            'email_server': {
                'host': current_app.config.get('MAIL_SERVER'),
                'port': current_app.config.get('MAIL_PORT', 587),
                'config_key': 'MAIL_SERVER'
            }
        }
        
        results = {}
        overall_status = 'healthy'
        
        def check_http_service(name, url):
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    return {'status': 'healthy', 'message': f'{name} accessible'}
                else:
                    return {'status': 'degraded', 'message': f'{name} returned status {response.status_code}'}
            except Exception as e:
                return {'status': 'unhealthy', 'message': f'{name} not accessible: {str(e)}'}
        
        def check_tcp_service(name, host, port):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                result = sock.connect_ex((host, port))
                sock.close()
                
                if result == 0:
                    return {'status': 'healthy', 'message': f'{name} accessible'}
                else:
                    return {'status': 'unhealthy', 'message': f'{name} not accessible'}
            except Exception as e:
                return {'status': 'unhealthy', 'message': f'{name} check failed: {str(e)}'}
        
        for service_name, config in services.items():
            if config.get('config_key') and current_app.config.get(config['config_key']):
                if 'url' in config:
                    result = check_http_service(service_name, config['url'])
                elif 'host' in config and 'port' in config:
                    result = check_tcp_service(service_name, config['host'], config['port'])
                else:
                    result = {'status': 'not_configured', 'message': f'{service_name} not properly configured'}
            else:
                result = {'status': 'not_configured', 'message': f'{service_name} not configured'}
            
            results[service_name] = result
            
            # Update overall status
            if result['status'] == 'unhealthy':
                overall_status = 'degraded'  # External services are not critical
        
        return {
            'status': overall_status,
            'message': f'External services status: {overall_status}',
            'details': results
        }
    
    def check_application_health(self):
        """Check application-specific health metrics"""
        try:
            from app.models import User, Property, Task
            
            details = {}
            warnings = []
            
            # Check if we can query core models
            try:
                user_count = User.query.count()
                details['user_count'] = user_count
            except Exception as e:
                warnings.append(f'Cannot query users: {str(e)}')
            
            try:
                property_count = Property.query.count()
                details['property_count'] = property_count
            except Exception as e:
                warnings.append(f'Cannot query properties: {str(e)}')
            
            try:
                task_count = Task.query.count()
                details['task_count'] = task_count
            except Exception as e:
                warnings.append(f'Cannot query tasks: {str(e)}')
            
            # Check for recent activity
            try:
                recent_tasks = Task.query.filter(
                    Task.created_at >= datetime.utcnow() - timedelta(hours=24)
                ).count() if hasattr(Task, 'created_at') else None
                
                if recent_tasks is not None:
                    details['recent_tasks_24h'] = recent_tasks
            except Exception as e:
                warnings.append(f'Cannot check recent activity: {str(e)}')
            
            # Determine status
            status = 'healthy'
            message = 'Application functioning normally'
            
            if warnings:
                status = 'degraded'
                message = f'Application has issues: {len(warnings)} warnings'
                details['warnings'] = warnings
            
            return {
                'status': status,
                'message': message,
                'details': details
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'message': f'Application health check failed: {str(e)}',
                'details': {'error': str(e)}
            }
    
    def run_all_checks(self, parallel=True):
        """Run all health checks"""
        start_time = time.time()
        results = {}
        overall_status = 'healthy'
        
        if parallel:
            # Run checks in parallel for better performance
            with ThreadPoolExecutor(max_workers=len(self.checks)) as executor:
                future_to_check = {
                    executor.submit(check_func): check_name
                    for check_name, check_func in self.checks.items()
                }
                
                for future in as_completed(future_to_check, timeout=self.timeout):
                    check_name = future_to_check[future]
                    try:
                        result = future.result(timeout=5)
                        results[check_name] = result
                    except Exception as e:
                        results[check_name] = {
                            'status': 'unhealthy',
                            'message': f'Health check failed: {str(e)}',
                            'details': {'error': str(e)}
                        }
        else:
            # Run checks sequentially
            for check_name, check_func in self.checks.items():
                try:
                    result = check_func()
                    results[check_name] = result
                except Exception as e:
                    results[check_name] = {
                        'status': 'unhealthy',
                        'message': f'Health check failed: {str(e)}',
                        'details': {'error': str(e)}
                    }
        
        # Determine overall status
        for check_name, result in results.items():
            if result['status'] == 'unhealthy':
                overall_status = 'unhealthy'
                break
            elif result['status'] == 'degraded' and overall_status != 'unhealthy':
                overall_status = 'degraded'
        
        total_time = time.time() - start_time
        
        return {
            'status': overall_status,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'duration_seconds': total_time,
            'checks': results,
            'summary': {
                'total_checks': len(results),
                'healthy': sum(1 for r in results.values() if r['status'] == 'healthy'),
                'degraded': sum(1 for r in results.values() if r['status'] == 'degraded'),
                'unhealthy': sum(1 for r in results.values() if r['status'] == 'unhealthy'),
                'not_configured': sum(1 for r in results.values() if r['status'] == 'not_configured')
            }
        }

def create_health_endpoints(app):
    """Create health check endpoints"""
    
    health_checker = HealthChecker()
    
    @app.route('/health')
    def health_check():
        """Basic health check endpoint"""
        try:
            results = health_checker.run_all_checks(parallel=True)
            
            status_code = 200
            if results['status'] == 'unhealthy':
                status_code = 503
            elif results['status'] == 'degraded':
                status_code = 200  # Still operational
            
            return jsonify(results), status_code
            
        except Exception as e:
            logger.error(f"Health check endpoint failed: {e}", exc_info=True)
            return jsonify({
                'status': 'unhealthy',
                'message': 'Health check system failure',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }), 503
    
    @app.route('/health/live')
    def liveness_check():
        """Kubernetes liveness probe - basic app responsiveness"""
        return jsonify({
            'status': 'healthy',
            'message': 'Application is running',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 200
    
    @app.route('/health/ready')
    def readiness_check():
        """Kubernetes readiness probe - app ready to serve traffic"""
        try:
            # Only check critical components for readiness
            critical_checks = ['database', 'cache']
            results = {}
            
            for check_name in critical_checks:
                if check_name in health_checker.checks:
                    results[check_name] = health_checker.checks[check_name]()
            
            # Check if any critical component is unhealthy
            unhealthy_components = [
                name for name, result in results.items()
                if result['status'] == 'unhealthy'
            ]
            
            if unhealthy_components:
                return jsonify({
                    'status': 'not_ready',
                    'message': f'Critical components unhealthy: {", ".join(unhealthy_components)}',
                    'checks': results,
                    'timestamp': datetime.utcnow().isoformat() + 'Z'
                }), 503
            
            return jsonify({
                'status': 'ready',
                'message': 'Application ready to serve traffic',
                'checks': results,
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }), 200
            
        except Exception as e:
            logger.error(f"Readiness check failed: {e}", exc_info=True)
            return jsonify({
                'status': 'not_ready',
                'message': 'Readiness check failed',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }), 503

def init_health_checks(app):
    """Initialize health checks for the Flask app"""
    if app.config.get('HEALTH_CHECK_ENABLED', True):
        create_health_endpoints(app)
        logger.info("Health check endpoints initialized")
    else:
        logger.info("Health checks disabled by configuration")