"""
Business Analytics Dashboard Routes
Provides revenue, occupancy, and performance metrics for property owners
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from datetime import datetime, timedelta, date
from sqlalchemy import func, extract, and_, or_
import calendar
from collections import defaultdict

from app import db
from app.models import (
    Property, CalendarEvent, Invoice, InvoiceItem, 
    BookingTask, GuestBooking, User, UserRoles
)
from app.utils.decorators import property_owner_required

bp = Blueprint('analytics', __name__, url_prefix='/analytics')

@bp.route('/dashboard')
@login_required
def business_dashboard():
    """Main business analytics dashboard"""
    
    # Check if user has permission
    if not (current_user.is_property_owner or current_user.has_admin_role or current_user.is_property_manager):
        flash('Access denied. Business analytics is only available to property owners and managers.', 'error')
        return redirect(url_for('main.dashboard'))
    
    # Get properties based on user role
    if current_user.has_admin_role:
        properties = Property.query.all()
    elif current_user.is_property_owner:
        properties = Property.query.filter_by(owner_id=current_user.id).all()
    elif current_user.is_property_manager:
        properties = current_user.managed_properties
    else:
        properties = []
    
    # Get date range from request or default to current month
    year = request.args.get('year', datetime.now().year, type=int)
    month = request.args.get('month', datetime.now().month, type=int)
    
    # Calculate date range
    start_date = date(year, month, 1)
    _, last_day = calendar.monthrange(year, month)
    end_date = date(year, month, last_day)
    
    # Initialize metrics
    metrics = {
        'total_revenue': 0,
        'total_bookings': 0,
        'occupancy_rate': 0,
        'avg_booking_value': 0,
        'properties_count': len(properties),
        'revenue_by_property': {},
        'occupancy_by_property': {},
        'monthly_revenue': [],
        'booking_sources': defaultdict(int),
        'year': year,
        'month': month,
        'month_name': calendar.month_name[month]
    }
    
    # Calculate metrics for each property
    for prop in properties:
        property_metrics = calculate_property_metrics(prop.id, start_date, end_date)
        
        metrics['total_revenue'] += property_metrics['revenue']
        metrics['total_bookings'] += property_metrics['bookings_count']
        metrics['revenue_by_property'][prop.name] = property_metrics['revenue']
        metrics['occupancy_by_property'][prop.name] = property_metrics['occupancy_rate']
        
        # Aggregate booking sources
        for source, count in property_metrics['booking_sources'].items():
            metrics['booking_sources'][source] += count
    
    # Calculate averages
    if metrics['total_bookings'] > 0:
        metrics['avg_booking_value'] = metrics['total_revenue'] / metrics['total_bookings']
    
    if len(properties) > 0:
        total_occupancy = sum(metrics['occupancy_by_property'].values())
        metrics['occupancy_rate'] = total_occupancy / len(properties)
    
    # Get last 12 months revenue trend
    metrics['monthly_revenue'] = get_monthly_revenue_trend(properties, 12)
    
    # Get upcoming bookings
    metrics['upcoming_bookings'] = get_upcoming_bookings(properties, 7)
    
    # Get top performing properties
    metrics['top_properties'] = sorted(
        metrics['revenue_by_property'].items(), 
        key=lambda x: x[1], 
        reverse=True
    )[:5]
    
    return render_template('analytics/dashboard.html', 
                         properties=properties,
                         metrics=metrics,
                         current_year=datetime.now().year)


def calculate_property_metrics(property_id, start_date, end_date):
    """Calculate metrics for a single property"""
    
    metrics = {
        'revenue': 0,
        'bookings_count': 0,
        'occupancy_rate': 0,
        'booking_sources': defaultdict(int),
        'booked_nights': 0,
        'available_nights': (end_date - start_date).days + 1
    }
    
    # Get calendar events for this property in date range
    events = CalendarEvent.query.filter(
        CalendarEvent.property_id == property_id,
        CalendarEvent.start_date <= end_date,
        CalendarEvent.end_date >= start_date
    ).all()
    
    # Calculate booked nights and booking sources
    for event in events:
        # Calculate overlap with our date range
        event_start = max(event.start_date, start_date)
        event_end = min(event.end_date, end_date)
        
        if event_start <= event_end:
            nights = (event_end - event_start).days + 1
            metrics['booked_nights'] += nights
            metrics['bookings_count'] += 1
            
            # Track booking source
            source = event.source or 'direct'
            metrics['booking_sources'][source] += 1
            
            # Estimate revenue (if booking amount is available)
            if event.booking_amount:
                metrics['revenue'] += float(event.booking_amount)
    
    # Get invoices for revenue calculation (if calendar events don't have amounts)
    if metrics['revenue'] == 0:
        invoices = Invoice.query.filter(
            Invoice.property_id == property_id,
            Invoice.created_at >= datetime.combine(start_date, datetime.min.time()),
            Invoice.created_at <= datetime.combine(end_date, datetime.max.time()),
            Invoice.status == 'paid'
        ).all()
        
        for invoice in invoices:
            metrics['revenue'] += float(invoice.total_amount or 0)
    
    # Calculate occupancy rate
    if metrics['available_nights'] > 0:
        metrics['occupancy_rate'] = (metrics['booked_nights'] / metrics['available_nights']) * 100
    
    return metrics


def get_monthly_revenue_trend(properties, months=12):
    """Get revenue trend for the last N months"""
    
    trend_data = []
    today = date.today()
    
    for i in range(months - 1, -1, -1):
        # Calculate month start
        month_date = today - timedelta(days=i * 30)
        year = month_date.year
        month = month_date.month
        
        start_date = date(year, month, 1)
        _, last_day = calendar.monthrange(year, month)
        end_date = date(year, month, last_day)
        
        # Calculate total revenue for this month
        month_revenue = 0
        for prop in properties:
            prop_metrics = calculate_property_metrics(prop.id, start_date, end_date)
            month_revenue += prop_metrics['revenue']
        
        trend_data.append({
            'month': calendar.month_abbr[month],
            'year': year,
            'revenue': month_revenue
        })
    
    return trend_data


def get_upcoming_bookings(properties, days=7):
    """Get upcoming bookings in the next N days"""
    
    upcoming = []
    today = date.today()
    future_date = today + timedelta(days=days)
    
    for prop in properties:
        events = CalendarEvent.query.filter(
            CalendarEvent.property_id == prop.id,
            CalendarEvent.start_date >= today,
            CalendarEvent.start_date <= future_date
        ).order_by(CalendarEvent.start_date).all()
        
        for event in events:
            upcoming.append({
                'property': prop.name,
                'guest': event.guest_name or 'Guest',
                'check_in': event.start_date,
                'check_out': event.end_date,
                'source': event.source or 'direct',
                'amount': event.booking_amount
            })
    
    return sorted(upcoming, key=lambda x: x['check_in'])


@bp.route('/api/property-metrics/<int:property_id>')
@login_required
def api_property_metrics(property_id):
    """API endpoint for property-specific metrics"""
    
    # Verify access
    property = Property.query.get_or_404(property_id)
    if not (current_user.has_admin_role or 
            property.owner_id == current_user.id or
            current_user in property.managers):
        return jsonify({'error': 'Access denied'}), 403
    
    # Get date range from request
    year = request.args.get('year', datetime.now().year, type=int)
    month = request.args.get('month', datetime.now().month, type=int)
    
    start_date = date(year, month, 1)
    _, last_day = calendar.monthrange(year, month)
    end_date = date(year, month, last_day)
    
    # Calculate metrics
    metrics = calculate_property_metrics(property_id, start_date, end_date)
    
    # Add property info
    metrics['property_name'] = property.name
    metrics['property_address'] = property.get_full_address()
    
    return jsonify(metrics)


@bp.route('/api/revenue-chart')
@login_required
def api_revenue_chart():
    """API endpoint for revenue chart data"""
    
    # Get user's properties
    if current_user.has_admin_role:
        properties = Property.query.all()
    elif current_user.is_property_owner:
        properties = Property.query.filter_by(owner_id=current_user.id).all()
    elif current_user.is_property_manager:
        properties = current_user.managed_properties
    else:
        return jsonify({'error': 'Access denied'}), 403
    
    # Get time period from request
    period = request.args.get('period', '6months')
    
    if period == '30days':
        months = 1
    elif period == '3months':
        months = 3
    elif period == '6months':
        months = 6
    elif period == '12months':
        months = 12
    else:
        months = 6
    
    # Get revenue trend
    trend_data = get_monthly_revenue_trend(properties, months)
    
    return jsonify({
        'labels': [f"{d['month']} {d['year']}" for d in trend_data],
        'data': [d['revenue'] for d in trend_data]
    })


@bp.route('/export')
@login_required
def export_analytics():
    """Export analytics data to CSV"""
    
    # This would generate a CSV file with analytics data
    # Implementation depends on specific requirements
    
    flash('Export functionality coming soon!', 'info')
    return redirect(url_for('analytics.business_dashboard'))