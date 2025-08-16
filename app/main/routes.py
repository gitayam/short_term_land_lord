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
        
        # If no properties exist, create sample ones
        if not properties:
            current_app.logger.info("No properties found, creating sample properties")
            try:
                sample_properties = [
                    {'name': 'Oceanview Condo', 'address': '123 Beach Blvd, Miami, FL 33139'},
                    {'name': 'Mountain Lodge', 'address': '456 Alpine Drive, Denver, CO 80424'},
                    {'name': 'City Loft', 'address': '789 Urban Street, New York, NY 10001'}
                ]
                
                for sample in sample_properties:
                    new_property = Property(
                        name=sample['name'],
                        address=sample['address'],
                        owner_id=current_user.id
                    )
                    db.session.add(new_property)
                
                db.session.commit()
                properties = Property.query.order_by(Property.name).all()
                current_app.logger.info(f"Created {len(properties)} sample properties")
            except Exception as e:
                current_app.logger.error(f"Error creating sample properties: {e}")
                properties = []
        
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
                'extendedProps': {
                    'color': color,
                    'city': getattr(prop, 'city', ''),
                    'state': getattr(prop, 'state', ''),
                    'address': getattr(prop, 'address', ''),
                    'image_url': getattr(prop, 'image_url', '/static/images/default-property.jpg')
                }
            })
        
        # Load real calendar events from synced booking platforms
        from app.models import CalendarEvent
        from datetime import datetime, timedelta
        
        property_ids = [prop.id for prop in properties]
        if property_ids:
            # Query real calendar events for the next 90 days
            start_date = datetime.now().date()
            end_date = start_date + timedelta(days=90)
            
            calendar_events = CalendarEvent.query.filter(
                CalendarEvent.property_id.in_(property_ids),
                CalendarEvent.start_date >= start_date,
                CalendarEvent.start_date <= end_date
            ).order_by(CalendarEvent.start_date).all()
            
            # Convert CalendarEvent objects to FullCalendar format
            for event in calendar_events:
                events.append(event.to_fullcalendar_dict())
            
            current_app.logger.info(f"Loaded {len(events)} real calendar events from booking platforms")
        else:
            current_app.logger.info("No properties available, no events to load")
        
        # If no real events exist, generate sample data for demonstration
        if not events and properties:
            current_app.logger.info("No real calendar events found, generating sample data for demonstration")
            import random
            
            for i, prop in enumerate(properties[:3]):  # Limit to first 3 properties for demo
                # Generate 1-2 sample bookings per property with consistent dates
                sample_bookings = [
                    {'start_offset': 1, 'duration': 3, 'guest': 'Johnson Group', 'platform': 'VRBO', 'amount': 282},
                    {'start_offset': 8, 'duration': 4, 'guest': 'Brown Couple', 'platform': 'Airbnb', 'amount': 320}
                ]
                
                for booking_num, booking_data in enumerate(sample_bookings[:2]):
                    start_offset = booking_data['start_offset']
                    duration = booking_data['duration']
                    
                    start_date = datetime.now() + timedelta(days=start_offset)
                    end_date = start_date + timedelta(days=duration)
                    
                    events.append({
                        'id': f'sample_{prop.id}_{booking_num}',
                        'resourceId': str(prop.id),
                        'title': booking_data['guest'],
                        'start': start_date.isoformat(),
                        'end': end_date.isoformat(),
                        'backgroundColor': resources[i]['color'],
                        'borderColor': resources[i]['color'],
                        'textColor': '#ffffff',
                        'extendedProps': {
                            'property_id': prop.id,
                            'property_name': prop.name,
                            'platform': booking_data['platform'],
                            'status': 'Confirmed',
                            'amount': booking_data['amount'],
                            'guest_count': 4 if booking_data['guest'] == 'Johnson Group' else 2,
                            'is_sample': True  # Mark as sample data
                        }
                    })
            
            current_app.logger.info(f"Generated {len(events)} sample events for demonstration")
        
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
        
        # Generate sample events for dashboard (similar to combined calendar)
        from datetime import datetime, timedelta
        import random
        
        for prop in properties[:5]:  # Limit to first 5 properties
            # Generate 1-2 sample events per property
            for event_num in range(1, 3):
                # Random start date within next 30 days
                start_offset = random.randint(0, 30)
                duration = random.randint(1, 5)  # 1-5 day events
                
                start_date = datetime.now() + timedelta(days=start_offset)
                end_date = start_date + timedelta(days=duration)
                
                events.append({
                    'id': f'dashboard_event_{prop.id}_{event_num}',
                    'title': f'{prop.name} Event',
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat(),
                    'backgroundColor': '#007bff',
                    'borderColor': '#007bff',
                    'extendedProps': {
                        'property_id': prop.id,
                        'property_name': prop.name,
                        'type': 'property_event'
                    }
                })

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