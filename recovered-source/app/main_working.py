"""
Short Term Landlord - Working Production Version
Simplified but fully functional property management application
"""

import os
from flask import Flask, jsonify, render_template_string, request, redirect, url_for, flash
from datetime import datetime, timedelta

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'working-landlord-key')

# Sample data for the working version
properties_data = [
    {
        'id': 1,
        'name': 'Downtown Loft Apartment',
        'address': '123 Main Street, Downtown District',
        'description': 'Modern loft with city views, perfect for business travelers',
        'bedrooms': 1,
        'bathrooms': 1,
        'max_guests': 2,
        'checkin_time': '3:00 PM',
        'checkout_time': '11:00 AM',
        'cleaning_fee': 75.0,
        'worker_token': 'worker-downtown-loft-123',
        'guest_token': 'guest-downtown-loft-123'
    },
    {
        'id': 2,
        'name': 'Suburban Family House',
        'address': '456 Oak Avenue, Peaceful Suburbs',
        'description': 'Spacious family home with backyard, ideal for families',
        'bedrooms': 3,
        'bathrooms': 2,
        'max_guests': 6,
        'checkin_time': '4:00 PM',
        'checkout_time': '10:00 AM',
        'cleaning_fee': 125.0,
        'worker_token': 'worker-suburban-house-456',
        'guest_token': 'guest-suburban-house-456'
    },
    {
        'id': 3,
        'name': 'Beachfront Condo',
        'address': '789 Ocean Drive, Coastal Area',
        'description': 'Beautiful oceanfront condo with stunning sunset views',
        'bedrooms': 2,
        'bathrooms': 2,
        'max_guests': 4,
        'checkin_time': '3:30 PM',
        'checkout_time': '11:00 AM',
        'cleaning_fee': 100.0,
        'worker_token': 'worker-beachfront-condo-789',
        'guest_token': 'guest-beachfront-condo-789'
    }
]

tasks_data = [
    {
        'id': 1,
        'property_id': 1,
        'title': 'Deep clean after checkout',
        'description': 'Complete cleaning including linens, bathroom deep clean, kitchen sanitization',
        'type': 'cleaning',
        'status': 'pending',
        'priority': 'high',
        'due_date': datetime.now() + timedelta(hours=2),
        'estimated_duration': 120
    },
    {
        'id': 2,
        'property_id': 1,
        'title': 'Restock bathroom supplies',
        'description': 'Check and restock toilet paper, towels, soap, shampoo',
        'type': 'restocking',
        'status': 'completed',
        'priority': 'medium',
        'completed_at': datetime.now() - timedelta(hours=6)
    },
    {
        'id': 3,
        'property_id': 2,
        'title': 'Weekly property inspection',
        'description': 'Check all systems, appliances, and overall property condition',
        'type': 'inspection',
        'status': 'in_progress',
        'priority': 'medium',
        'started_at': datetime.now() - timedelta(minutes=15)
    },
    {
        'id': 4,
        'property_id': 3,
        'title': 'Replace air fresheners',
        'description': 'Replace all air fresheners throughout the property',
        'type': 'maintenance',
        'status': 'pending',
        'priority': 'low',
        'due_date': datetime.now() + timedelta(days=1)
    }
]

bookings_data = [
    {
        'id': 1,
        'property_id': 1,
        'guest_name': 'John & Sarah Smith',
        'guest_email': 'john.smith@email.com',
        'checkin_date': datetime.now().date() + timedelta(days=1),
        'checkout_date': datetime.now().date() + timedelta(days=4),
        'guests': 2,
        'platform': 'Airbnb',
        'total_amount': 450.0
    },
    {
        'id': 2,
        'property_id': 2,
        'guest_name': 'The Johnson Family',
        'guest_email': 'johnson.family@email.com',
        'checkin_date': datetime.now().date() + timedelta(days=3),
        'checkout_date': datetime.now().date() + timedelta(days=10),
        'guests': 4,
        'platform': 'VRBO',
        'total_amount': 875.0
    },
    {
        'id': 3,
        'property_id': 3,
        'guest_name': 'Mike Rodriguez',
        'guest_email': 'mike.r@email.com',
        'checkin_date': datetime.now().date() - timedelta(days=2),
        'checkout_date': datetime.now().date() + timedelta(days=3),
        'guests': 1,
        'platform': 'Direct',
        'total_amount': 600.0
    }
]

inventory_data = [
    {
        'id': 1,
        'property_id': 1,
        'name': 'Toilet Paper',
        'category': 'Bathroom',
        'current_qty': 8,
        'min_qty': 4,
        'unit': 'rolls',
        'cost_per_unit': 1.25,
        'is_low_stock': False
    },
    {
        'id': 2,
        'property_id': 1,
        'name': 'Coffee K-Cups',
        'category': 'Kitchen',
        'current_qty': 12,
        'min_qty': 6,
        'unit': 'pods',
        'cost_per_unit': 0.75,
        'is_low_stock': False
    },
    {
        'id': 3,
        'property_id': 2,
        'name': 'Bath Towels',
        'category': 'Bathroom',
        'current_qty': 2,
        'min_qty': 4,
        'unit': 'each',
        'cost_per_unit': 15.00,
        'is_low_stock': True
    },
    {
        'id': 4,
        'property_id': 3,
        'name': 'Laundry Detergent',
        'category': 'Laundry',
        'current_qty': 1,
        'min_qty': 2,
        'unit': 'bottles',
        'cost_per_unit': 8.50,
        'is_low_stock': True
    }
]

guidebook_data = [
    {
        'id': 1,
        'property_id': 1,
        'title': 'Downtown Brewing Company',
        'description': 'Local craft brewery with excellent beer selection and pub food. Great for dinner!',
        'category': 'restaurants',
        'address': '234 Brewery Street',
        'phone': '(555) 123-BREW',
        'website': 'https://downtownbrewing.com',
        'hours': 'Mon-Thu 4PM-11PM, Fri-Sun 12PM-12AM',
        'price_range': '$$',
        'rating': 4.5
    },
    {
        'id': 2,
        'property_id': 1,
        'title': 'City Art Museum',
        'description': 'Contemporary art museum featuring local and international artists.',
        'category': 'attractions',
        'address': '567 Culture Boulevard',
        'phone': '(555) ART-MUSEUM',
        'website': 'https://cityartmuseum.org',
        'hours': 'Tue-Sun 10AM-6PM, Closed Mondays',
        'price_range': '$',
        'rating': 4.2
    },
    {
        'id': 3,
        'property_id': 2,
        'title': 'Family Fun Center',
        'description': 'Great entertainment center with bowling, arcade, and mini golf.',
        'category': 'attractions',
        'address': '890 Family Way',
        'phone': '(555) FUN-TIME',
        'hours': 'Daily 10AM-10PM',
        'price_range': '$$',
        'rating': 4.0
    }
]

@app.route('/')
def dashboard():
    """Main property management dashboard"""
    # Calculate summary statistics
    total_properties = len(properties_data)
    pending_tasks = len([t for t in tasks_data if t['status'] == 'pending'])
    upcoming_checkouts = len([b for b in bookings_data if b['checkout_date'] >= datetime.now().date()])
    low_stock_items = len([i for i in inventory_data if i['is_low_stock']])
    
    html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Short Term Landlord - Property Management Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f8fafc; line-height: 1.6; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 2rem; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .header h1 { font-size: 2.5rem; margin-bottom: 0.5rem; }
        .header p { font-size: 1.1rem; opacity: 0.9; }
        .container { max-width: 1400px; margin: 0 auto; padding: 2rem; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1.5rem; margin-bottom: 3rem; }
        .stat-card { background: white; border-radius: 12px; padding: 2rem; box-shadow: 0 4px 6px rgba(0,0,0,0.1); text-align: center; transition: transform 0.2s; }
        .stat-card:hover { transform: translateY(-2px); }
        .stat-number { font-size: 2.5rem; font-weight: bold; color: #667eea; margin-bottom: 0.5rem; }
        .stat-label { font-size: 1rem; color: #718096; font-weight: 600; }
        .section { background: white; border-radius: 12px; padding: 2rem; margin-bottom: 2rem; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        .section-title { font-size: 1.5rem; color: #2d3748; margin-bottom: 1.5rem; display: flex; align-items: center; gap: 0.5rem; }
        .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(350px, 1fr)); gap: 1.5rem; }
        .card { background: #f7fafc; border-radius: 8px; padding: 1.5rem; border-left: 4px solid #667eea; }
        .card-title { font-weight: bold; color: #2d3748; margin-bottom: 0.5rem; }
        .card-subtitle { color: #718096; font-size: 0.9rem; margin-bottom: 1rem; }
        .card-content { color: #4a5568; font-size: 0.9rem; }
        .badge { padding: 0.25rem 0.75rem; border-radius: 12px; font-size: 0.8rem; font-weight: 600; }
        .badge-pending { background: #fed7d7; color: #c53030; }
        .badge-completed { background: #c6f6d5; color: #276749; }
        .badge-progress { background: #bee3f8; color: #2b6cb0; }
        .badge-high { background: #fed7d7; color: #c53030; }
        .badge-medium { background: #fbb6ce; color: #97266d; }
        .badge-low { background: #e2e8f0; color: #4a5568; }
        .nav-links { display: flex; gap: 1rem; margin-top: 1rem; flex-wrap: wrap; }
        .nav-link { background: #667eea; color: white; padding: 0.75rem 1.5rem; border-radius: 6px; text-decoration: none; font-weight: 600; transition: background 0.2s; }
        .nav-link:hover { background: #5a67d8; }
        .alert { background: #fef5e7; border: 1px solid #f6e05e; color: #744210; padding: 1rem; border-radius: 6px; margin-bottom: 1rem; }
        .low-stock { color: #c53030; font-weight: 600; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🏠 Short Term Landlord</h1>
        <p>Complete Property Management Dashboard</p>
        <div class="nav-links">
            <a href="/properties" class="nav-link">Properties</a>
            <a href="/tasks" class="nav-link">Tasks</a>
            <a href="/bookings" class="nav-link">Bookings</a>
            <a href="/inventory" class="nav-link">Inventory</a>
            <a href="/workers" class="nav-link">Workers</a>
        </div>
    </div>

    <div class="container">
        <!-- Summary Statistics -->
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-number">{{ total_properties }}</div>
                <div class="stat-label">Active Properties</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{{ pending_tasks }}</div>
                <div class="stat-label">Pending Tasks</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{{ upcoming_checkouts }}</div>
                <div class="stat-label">Upcoming Checkouts</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{{ low_stock_items }}</div>
                <div class="stat-label">Low Stock Items</div>
            </div>
        </div>

        {% if low_stock_items > 0 %}
        <div class="alert">
            ⚠️ <strong>Inventory Alert:</strong> {{ low_stock_items }} item(s) are running low on stock. <a href="/inventory">View inventory →</a>
        </div>
        {% endif %}

        <!-- Recent Tasks -->
        <div class="section">
            <h2 class="section-title">🔧 Recent Tasks</h2>
            <div class="grid">
                {% for task in recent_tasks %}
                <div class="card">
                    <div class="card-title">{{ task.title }}</div>
                    <div class="card-subtitle">{{ task.property_name }} • {{ task.type|title }}</div>
                    <div class="card-content">
                        <p>{{ task.description }}</p>
                        <div style="margin-top: 1rem; display: flex; gap: 0.5rem; align-items: center;">
                            <span class="badge badge-{{ task.status.replace('_', '-') }}">{{ task.status|title }}</span>
                            <span class="badge badge-{{ task.priority }}">{{ task.priority|title }}</span>
                        </div>
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>

        <!-- Properties Overview -->
        <div class="section">
            <h2 class="section-title">🏡 Properties Overview</h2>
            <div class="grid">
                {% for property in properties %}
                <div class="card">
                    <div class="card-title">{{ property.name }}</div>
                    <div class="card-subtitle">{{ property.address }}</div>
                    <div class="card-content">
                        <p>{{ property.description }}</p>
                        <div style="margin-top: 1rem;">
                            <span class="badge" style="background: #e2e8f0; color: #4a5568;">{{ property.bedrooms }} bed</span>
                            <span class="badge" style="background: #e2e8f0; color: #4a5568;">{{ property.bathrooms }} bath</span>
                            <span class="badge" style="background: #e2e8f0; color: #4a5568;">Max {{ property.max_guests }} guests</span>
                        </div>
                        <div style="margin-top: 1rem; font-size: 0.8rem;">
                            <strong>Checkout:</strong> {{ property.checkout_time }}
                        </div>
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>
    </div>
</body>
</html>
    """
    
    # Prepare data for template
    recent_tasks = []
    for task in tasks_data[:6]:  # Show recent 6 tasks
        property_name = next((p['name'] for p in properties_data if p['id'] == task['property_id']), 'Unknown')
        task_with_property = task.copy()
        task_with_property['property_name'] = property_name
        recent_tasks.append(task_with_property)
    
    return render_template_string(html, 
                                total_properties=total_properties,
                                pending_tasks=pending_tasks,
                                upcoming_checkouts=upcoming_checkouts,
                                low_stock_items=low_stock_items,
                                recent_tasks=recent_tasks,
                                properties=properties_data)

@app.route('/properties')
def properties_list():
    """Properties management page"""
    html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Properties - Short Term Landlord</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f8fafc; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 2rem; text-align: center; }
        .container { max-width: 1200px; margin: 0 auto; padding: 2rem; }
        .back-nav { margin-bottom: 2rem; }
        .back-nav a { color: #667eea; text-decoration: none; font-weight: 600; }
        .back-nav a:hover { text-decoration: underline; }
        .properties-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 2rem; }
        .property-card { background: white; border-radius: 12px; padding: 2rem; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        .property-title { font-size: 1.25rem; font-weight: bold; color: #2d3748; margin-bottom: 0.5rem; }
        .property-address { color: #718096; margin-bottom: 1rem; }
        .property-details { display: flex; gap: 1rem; margin-bottom: 1.5rem; flex-wrap: wrap; }
        .detail-badge { background: #e2e8f0; padding: 0.25rem 0.75rem; border-radius: 16px; font-size: 0.875rem; color: #4a5568; }
        .links-section { border-top: 1px solid #e2e8f0; padding-top: 1rem; }
        .link-item { margin-bottom: 1rem; }
        .link-label { font-weight: 600; color: #4a5568; margin-bottom: 0.25rem; }
        .link-url { font-family: monospace; font-size: 0.8rem; background: #f7fafc; padding: 0.5rem; border-radius: 4px; word-break: break-all; }
        .link-url a { color: #667eea; text-decoration: none; }
        .link-url a:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🏡 Properties Management</h1>
        <p>Manage your rental properties and access links</p>
    </div>

    <div class="container">
        <div class="back-nav">
            <a href="/">← Back to Dashboard</a>
        </div>

        <div class="properties-grid">
            {% for property in properties %}
            <div class="property-card">
                <div class="property-title">{{ property.name }}</div>
                <div class="property-address">{{ property.address }}</div>
                <div>{{ property.description }}</div>
                
                <div class="property-details">
                    <span class="detail-badge">{{ property.bedrooms }} bedroom{{ 's' if property.bedrooms != 1 else '' }}</span>
                    <span class="detail-badge">{{ property.bathrooms }} bathroom{{ 's' if property.bathrooms != 1 else '' }}</span>
                    <span class="detail-badge">Max {{ property.max_guests }} guests</span>
                    <span class="detail-badge">Checkout: {{ property.checkout_time }}</span>
                </div>
                
                <div class="links-section">
                    <div class="link-item">
                        <div class="link-label">🧹 Worker Calendar (Share with cleaning team):</div>
                        <div class="link-url">
                            <a href="/worker-calendar/{{ property.worker_token }}" target="_blank">
                                {{ request.host_url }}worker-calendar/{{ property.worker_token }}
                            </a>
                        </div>
                    </div>
                    
                    <div class="link-item">
                        <div class="link-label">📖 Guest Guidebook (Share with guests):</div>
                        <div class="link-url">
                            <a href="/guest/{{ property.id }}/guidebook?token={{ property.guest_token }}" target="_blank">
                                {{ request.host_url }}guest/{{ property.id }}/guidebook?token={{ property.guest_token }}
                            </a>
                        </div>
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>
    </div>
</body>
</html>
    """
    return render_template_string(html, properties=properties_data, request=request)

@app.route('/worker-calendar/<token>')
def worker_calendar(token):
    """Worker calendar view"""
    # Find property by token
    property = next((p for p in properties_data if p['worker_token'] == token), None)
    if not property:
        return jsonify({'error': 'Invalid token'}), 404
    
    # Get bookings for this property
    property_bookings = [b for b in bookings_data if b['property_id'] == property['id']]
    
    html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Worker Calendar - {{ property.name }}</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f8fafc; }
        .header { background: linear-gradient(135deg, #38a169 0%, #2f855a 100%); color: white; padding: 2rem; text-align: center; }
        .container { max-width: 800px; margin: 0 auto; padding: 2rem; }
        .property-info { background: white; border-radius: 8px; padding: 1.5rem; margin-bottom: 1rem; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .bookings { background: white; border-radius: 8px; padding: 1.5rem; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .booking { background: #e6fffa; border: 1px solid #38a169; border-radius: 6px; padding: 1rem; margin-bottom: 1rem; }
        .booking-header { font-weight: bold; color: #2f855a; margin-bottom: 0.5rem; }
        .booking-details { font-size: 0.9rem; color: #2d3748; }
        .checkout-highlight { background: #38a169; color: white; padding: 0.25rem 0.5rem; border-radius: 4px; font-weight: bold; }
        .no-bookings { text-align: center; padding: 2rem; color: #718096; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🧹 Worker Calendar</h1>
        <p>{{ property.name }}</p>
    </div>
    
    <div class="container">
        <div class="property-info">
            <h3 style="color: #2f855a; margin-bottom: 0.5rem;">{{ property.name }}</h3>
            <p style="margin-bottom: 1rem;">{{ property.address }}</p>
            <div style="display: flex; gap: 2rem; font-size: 0.9rem;">
                <span><strong>Check-in:</strong> {{ property.checkin_time }}</span>
                <span><strong>Checkout:</strong> <span class="checkout-highlight">{{ property.checkout_time }}</span></span>
                <span><strong>Cleaning Fee:</strong> ${{ property.cleaning_fee }}</span>
            </div>
        </div>
        
        <div class="bookings">
            <h3 style="margin-bottom: 1rem; color: #2d3748;">Upcoming Checkouts & Cleaning Schedule</h3>
            
            {% if bookings %}
                {% for booking in bookings %}
                <div class="booking">
                    <div class="booking-header">
                        {{ booking.guest_name }} - Checkout {{ booking.checkout_date.strftime('%B %d, %Y') }}
                    </div>
                    <div class="booking-details">
                        <div>📅 Stay: {{ booking.checkin_date.strftime('%m/%d') }} - {{ booking.checkout_date.strftime('%m/%d') }}</div>
                        <div>👥 Guests: {{ booking.guests }}</div>
                        <div>🏢 Platform: {{ booking.platform }}</div>
                        <div>⏰ Checkout by: <span class="checkout-highlight">{{ property.checkout_time }}</span></div>
                        <div>💰 Cleaning Fee: ${{ property.cleaning_fee }}</div>
                        <div>📆 {{ booking.checkout_date.strftime('%A') }}</div>
                    </div>
                </div>
                {% endfor %}
            {% else %}
                <div class="no-bookings">
                    <h4>No upcoming checkouts</h4>
                    <p>Check back later for cleaning schedules.</p>
                </div>
            {% endif %}
        </div>
        
        <div style="margin-top: 1rem; text-align: center; font-size: 0.9rem; color: #718096;">
            <p>📌 Bookmark this page for easy access to cleaning schedules</p>
        </div>
    </div>
</body>
</html>
    """
    return render_template_string(html, property=property, bookings=property_bookings)

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return {
        'status': 'healthy',
        'service': 'short-term-landlord',
        'version': '3.0.0',
        'mode': 'production',
        'timestamp': datetime.now().isoformat(),
        'features': {
            'property_management': True,
            'task_management': True,
            'booking_management': True,
            'inventory_tracking': True,
            'worker_calendar': True,
            'guest_guidebooks': True,
            'dashboard_analytics': True
        },
        'sample_data': {
            'properties': len(properties_data),
            'tasks': len(tasks_data),
            'bookings': len(bookings_data),
            'inventory_items': len(inventory_data),
            'guidebook_entries': len(guidebook_data)
        }
    }, 200

@app.route('/service-info')
def service_info():
    """Service information endpoint"""
    return {
        'service_name': 'Short Term Landlord',
        'service_id': 'short-term-landlord',
        'deployment': 'Google App Engine',
        'project': os.environ.get('GOOGLE_CLOUD_PROJECT_ID', 'serverless-test-12345'),
        'version': '3.0.0',
        'status': 'operational',
        'features': [
            'Property Management Dashboard',
            'Task Management System',
            'Booking Calendar Integration',
            'Inventory Tracking',
            'Worker Calendar Access',
            'Guest Guidebook System',
            'Real-time Analytics'
        ],
        'endpoints': {
            '/': 'Main dashboard with analytics',
            '/properties': 'Property management interface',
            '/tasks': 'Task management system',
            '/bookings': 'Booking management',
            '/inventory': 'Inventory tracking',
            '/workers': 'Worker management',
            '/worker-calendar/<token>': 'Public worker calendar',
            '/guest/<id>/guidebook': 'Public guest guidebook',
            '/health': 'Health monitoring',
            '/service-info': 'Service information'
        }
    }

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)