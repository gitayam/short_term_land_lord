from flask import render_template, current_app, flash, abort, jsonify, request, g
from flask_login import login_required, current_user
from app.main import bp
from app.models import Property, PropertyCalendar, UserRoles, Booking, BookingTask, db
from app.utils.cache_service import CacheService
try:
    from app.utils.validation import validate_query_params, SearchSchema
except ImportError:
    def validate_query_params(schema_class):
        def decorator(func):
            return func
        return decorator
    class SearchSchema:
        pass
from datetime import datetime, timedelta
import requests
try:
    from icalendar import Calendar
except ImportError:
    Calendar = None
import json
from sqlalchemy import or_
import time

@bp.route('/')
@bp.route('/index')
def index():
    return render_template('main/index.html', title='Home')

@bp.route('/dashboard')
@login_required
def dashboard():
    """Enhanced dashboard with caching and performance monitoring"""
    start_time = time.time()
    
    try:
        # Use cached dashboard data for better performance
        dashboard_data = CacheService.get_user_dashboard_data(current_user.id)
        
        if dashboard_data:
            current_app.logger.info(
                f"Dashboard loaded from cache for user {current_user.id}",
                extra={'request_id': getattr(g, 'request_id', None)}
            )
            
            # Get task summary
            task_summary = CacheService.get_user_task_summary(current_user.id)
            
            # Get property statistics for each property
            property_stats = {}
            for prop in dashboard_data.get('properties', []):
                stats = CacheService.get_property_statistics(prop['id'])
                if stats:
                    property_stats[prop['id']] = stats
            
            response_time = time.time() - start_time
            current_app.logger.info(
                f"Dashboard rendered in {response_time:.3f}s",
                extra={
                    'request_id': getattr(g, 'request_id', None),
                    'response_time': response_time,
                    'cache_hit': True
                }
            )
            
            return render_template(
                'main/dashboard.html', 
                title='Dashboard',
                dashboard_data=dashboard_data,
                task_summary=task_summary,
                property_stats=property_stats
            )
        
        # Fallback to database query if cache miss
        current_app.logger.warning(
            f"Cache miss for dashboard user {current_user.id}, falling back to database",
            extra={'request_id': getattr(g, 'request_id', None)}
        )
        
        # Get all properties based on user role
        if current_user.has_admin_role or current_user.is_property_manager:
            properties = Property.query.all()
        elif current_user.is_property_owner:
            properties = Property.query.filter_by(owner_id=current_user.id).all()
        elif current_user.is_service_staff:
            properties = [p for p in Property.query.all() if p.is_visible_to(current_user)]
        else:
            properties = []
        
        # Warm the cache for next time
        try:
            CacheService.warm_cache(current_user.id)
        except Exception as e:
            current_app.logger.error(f"Failed to warm cache: {e}")
        
        response_time = time.time() - start_time
        current_app.logger.info(
            f"Dashboard rendered in {response_time:.3f}s",
            extra={
                'request_id': getattr(g, 'request_id', None),
                'response_time': response_time,
                'cache_hit': False
            }
        )
        
        return render_template('main/dashboard.html', title='Dashboard', properties=properties)
        
    except Exception as e:
        current_app.logger.error(
            f"Dashboard error for user {current_user.id}: {str(e)}",
            extra={'request_id': getattr(g, 'request_id', None)},
            exc_info=True
        )
        flash('Error loading dashboard. Please try again.', 'error')
        return render_template('main/dashboard.html', title='Dashboard', properties=[])

@bp.route('/combined-calendar')
@login_required
@validate_query_params(SearchSchema)
def combined_calendar():
    """Enhanced combined calendar with validation and caching"""
    start_time = time.time()
    
    try:
        # Get validated query parameters
        search_params = getattr(request, 'validated_data', {})
        current_app.logger.debug(f"Calendar search params: {search_params}")
        
        # Get all properties if admin or property manager
        if current_user.has_admin_role or current_user.is_property_manager:
            properties = Property.query.order_by(Property.name).all()
        # Property owners see only their properties
        elif current_user.is_property_owner:
            properties = Property.query.filter_by(owner_id=current_user.id).order_by(Property.name).all()
        # Service staff see properties they have tasks for
        elif current_user.is_service_staff:
            properties = [p for p in Property.query.order_by(Property.name).all() if p.is_visible_to(current_user)]
        else:
            properties = []
        
        if not properties:
            flash('No properties found.', 'warning')
            return render_template('main/combined_calendar.html', title='Combined Calendar', properties=[])
        
        response_time = time.time() - start_time
        current_app.logger.info(
            f"Combined calendar loaded in {response_time:.3f}s",
            extra={
                'request_id': getattr(g, 'request_id', None),
                'response_time': response_time,
                'property_count': len(properties)
            }
        )
        
        return render_template('main/combined_calendar.html', title='Combined Calendar', properties=properties)
        
    except Exception as e:
        current_app.logger.error(
            f"Combined calendar error: {str(e)}",
            extra={'request_id': getattr(g, 'request_id', None)},
            exc_info=True
        )
        flash('Error loading calendar. Please try again.', 'error')
        return render_template('main/combined_calendar.html', title='Combined Calendar', properties=[])

@bp.route('/dashboard/events')
@login_required
def dashboard_events():
    try:
        # Get properties based on user role
        if current_user.has_admin_role or current_user.is_property_manager:
            properties = Property.query.all()
        elif current_user.is_property_owner:
            properties = Property.query.filter_by(owner_id=current_user.id).all()
        elif current_user.is_service_staff:
            # Get properties where user has tasks
            task_properties = db.session.query(Property).join(Booking).join(BookingTask).filter(
                BookingTask.assigned_to_id == current_user.id
            ).distinct().all()
            properties = [p for p in task_properties if p.is_visible_to(current_user)]
        else:
            properties = []

        if not properties:
            return jsonify([])

        # Get all upcoming bookings for these properties
        property_ids = [p.id for p in properties]
        bookings = Booking.query.filter(
            Booking.property_id.in_(property_ids),
            Booking.end_date >= datetime.now().date()
        ).all()

        events = [booking.to_dict() for booking in bookings]
        return jsonify(events)

    except Exception as e:
        current_app.logger.error(f"Error in dashboard_events: {str(e)}")
        return jsonify([])