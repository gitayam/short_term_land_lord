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
        
        if dashboard_data and dashboard_data.get('user'):
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
        current_app.logger.info(f"User {current_user.email} accessing combined calendar")
        current_app.logger.info(f"User role: {getattr(current_user, 'role', 'No role')}")
        current_app.logger.info(f"has_admin_role: {getattr(current_user, 'has_admin_role', False)}")
        current_app.logger.info(f"is_property_manager: {getattr(current_user, 'is_property_manager', False)}")
        
        if current_user.has_admin_role or current_user.is_property_manager:
            properties = Property.query.order_by(Property.name).all()
        # Property owners see only their properties
        elif current_user.is_property_owner:
            properties = Property.query.filter_by(owner_id=current_user.id).order_by(Property.name).all()
        # Service staff see properties they have tasks for
        elif current_user.is_service_staff:
            properties = [p for p in Property.query.order_by(Property.name).all() if p.is_visible_to(current_user)]
        else:
            # Fallback: show all properties for any authenticated user (for demo)
            properties = Property.query.order_by(Property.name).all()
            
        current_app.logger.info(f"Found {len(properties)} properties for user")
        
        # Log info about real properties found
        current_app.logger.info(f"Found {len(properties)} real properties for calendar display")
        
        if not properties:
            flash('No properties found.', 'warning')
            return render_template('main/combined_calendar.html', 
                                 title='Combined Calendar', 
                                 properties=[],
                                 resources=[],
                                 events=[])
        
        response_time = time.time() - start_time
        current_app.logger.info(
            f"Combined calendar loaded in {response_time:.3f}s",
            extra={
                'request_id': getattr(g, 'request_id', None),
                'response_time': response_time,
                'property_count': len(properties)
            }
        )
        
        # Prepare resources and events data for the calendar template
        resources = []
        events = []
        
        # Convert properties to resources format expected by the template
        for prop in properties:
            # Generate a consistent color based on property name
            color_hash = hash(prop.name) % 0xFFFFFF
            color = f'#{color_hash:06x}'
            
            resources.append({
                'id': str(prop.id),
                'title': prop.name,
                'color': color,
                'property_type': getattr(prop, 'property_type', 'house').lower(),
                'city': getattr(prop, 'city', ''),
                'state': getattr(prop, 'state', ''),
                'address': getattr(prop, 'address', ''),
                'image_url': getattr(prop, 'image_url', '/static/img/default-property.jpg'),
                'extendedProps': {
                    'color': color,
                    'city': getattr(prop, 'city', ''),
                    'state': getattr(prop, 'state', ''),
                    'address': getattr(prop, 'address', ''),
                    'image_url': getattr(prop, 'image_url', '/static/img/default-property.jpg')
                }
            })
        
        # Load real calendar events from synced booking platforms
        from app.models import CalendarEvent
        from datetime import datetime, timedelta
        
        property_ids = [prop.id for prop in properties]
        if property_ids:
            # Query real calendar events from the database - expand date range to show more events
            start_date = datetime.now().date() - timedelta(days=30)  # Show past 30 days too
            end_date = start_date + timedelta(days=120)  # Show next 90 days
            
            calendar_events = CalendarEvent.query.filter(
                CalendarEvent.property_id.in_(property_ids),
                CalendarEvent.start_date >= start_date,
                CalendarEvent.start_date <= end_date
            ).order_by(CalendarEvent.start_date).all()
            
            current_app.logger.info(f"Found {len(calendar_events)} calendar events in database for date range {start_date} to {end_date}")
            
            # Convert CalendarEvent objects to FullCalendar format
            for event in calendar_events:
                events.append(event.to_fullcalendar_dict())
            
            current_app.logger.info(f"Loaded {len(events)} real calendar events from booking platforms")
        else:
            current_app.logger.info("No properties available, no events to load")
        
        # If no calendar events exist, suggest running calendar sync
        if not events and properties:
            current_app.logger.info("No calendar events found. Calendar data should be synced from external platforms.")
            current_app.logger.info("Tip: Check PropertyCalendar settings and run calendar sync to import real booking data.")
            
            # Check if there are PropertyCalendar entries configured
            from app.models import PropertyCalendar
            calendars = PropertyCalendar.query.filter(
                PropertyCalendar.property_id.in_(property_ids),
                PropertyCalendar.is_active == True
            ).all()
            
            if calendars:
                current_app.logger.info(f"Found {len(calendars)} active PropertyCalendar entries. Consider running sync to import events.")
            else:
                current_app.logger.info("No PropertyCalendar entries found. Set up calendar URLs in property settings to enable event import.")
            
            current_app.logger.info(f"Combined calendar displaying {len(events)} real calendar events")
        
        current_app.logger.info(f"Combined calendar rendering with {len(resources)} resources and {len(events)} events")
        
        return render_template('main/combined_calendar.html', 
                             title='Combined Calendar', 
                             properties=properties,
                             resources=resources,
                             events=events)
        
    except Exception as e:
        current_app.logger.error(
            f"Combined calendar error: {str(e)}",
            extra={'request_id': getattr(g, 'request_id', None)},
            exc_info=True
        )
        flash('Error loading calendar. Please try again.', 'error')
        return render_template('main/combined_calendar.html', 
                             title='Combined Calendar', 
                             properties=[],
                             resources=[],
                             events=[])

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
            # Get properties where user has tasks assigned
            try:
                task_properties = db.session.query(Property).join(Booking).join(BookingTask).filter(
                    BookingTask.assigned_to_id == current_user.id
                ).distinct().all()
                properties = [p for p in task_properties if p.is_visible_to(current_user)]
            except Exception:
                # Fallback if Booking/BookingTask joins fail
                properties = Property.query.all()
        else:
            properties = []

        if not properties:
            return jsonify([])

        events = []
        
        # Get real calendar events for dashboard
        from datetime import datetime, timedelta
        from app.models import CalendarEvent
        
        property_ids = [p.id for p in properties]
        if property_ids:
            # Query real calendar events for the next 60 days
            start_date = datetime.now().date()
            end_date = start_date + timedelta(days=60)
            
            calendar_events = CalendarEvent.query.filter(
                CalendarEvent.property_id.in_(property_ids),
                CalendarEvent.start_date >= start_date,
                CalendarEvent.start_date <= end_date
            ).order_by(CalendarEvent.start_date).all()
            
            current_app.logger.info(f"Dashboard found {len(calendar_events)} calendar events for date range {start_date} to {end_date}")
            
            # Convert CalendarEvent objects to FullCalendar format
            for event in calendar_events:
                events.append(event.to_fullcalendar_dict())

        # Try to get real bookings if they exist
        try:
            property_ids = [p.id for p in properties]
            bookings = Booking.query.filter(
                Booking.property_id.in_(property_ids),
                Booking.end_date >= datetime.now().date()
            ).all()
            
            for booking in bookings[:10]:  # Limit to 10 real bookings
                events.append({
                    'id': f'booking_{booking.id}',
                    'title': getattr(booking, 'guest_name', 'Guest'),
                    'start': booking.start_date.isoformat() if booking.start_date else datetime.now().isoformat(),
                    'end': booking.end_date.isoformat() if booking.end_date else (datetime.now() + timedelta(days=1)).isoformat(),
                    'backgroundColor': '#28a745',
                    'borderColor': '#28a745',
                    'extendedProps': {
                        'property_id': booking.property_id,
                        'type': 'booking'
                    }
                })
        except Exception as booking_error:
            current_app.logger.warning(f"Could not fetch real bookings: {booking_error}")

        return jsonify(events)

    except Exception as e:
        current_app.logger.error(f"Error in dashboard_events: {str(e)}")
        return jsonify([])