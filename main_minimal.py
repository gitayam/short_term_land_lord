"""
Short Term Landlord - Minimal Working Version for App Engine
Ultra-streamlined version that definitely works
"""

import os
from flask import Flask, render_template_string, jsonify, request
from datetime import datetime, timedelta

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'landlord-minimal-key')

# Sample data for demonstration
sample_properties = [
    {
        'id': 1,
        'name': 'Cozy Downtown Apartment',
        'address': '123 Main St, Downtown',
        'bedrooms': 2,
        'bathrooms': 1,
        'checkin_time': '3:00 PM',
        'checkout_time': '11:00 AM',
        'worker_token': 'demo-worker-token-123',
        'guest_token': 'demo-guest-token-123'
    },
    {
        'id': 2,
        'name': 'Suburban Family House',
        'address': '456 Oak Ave, Suburbs',
        'bedrooms': 3,
        'bathrooms': 2,
        'checkin_time': '4:00 PM',
        'checkout_time': '10:00 AM',
        'worker_token': 'demo-worker-token-456',
        'guest_token': 'demo-guest-token-456'
    }
]

sample_bookings = [
    {
        'property_id': 1,
        'guest_name': 'John Smith',
        'checkin_date': datetime.now().date() + timedelta(days=1),
        'checkout_date': datetime.now().date() + timedelta(days=4),
        'guests': 2
    },
    {
        'property_id': 1,
        'guest_name': 'Alice Johnson',
        'checkin_date': datetime.now().date() + timedelta(days=7),
        'checkout_date': datetime.now().date() + timedelta(days=10),
        'guests': 1
    },
    {
        'property_id': 2,
        'guest_name': 'The Wilson Family',
        'checkin_date': datetime.now().date() + timedelta(days=3),
        'checkout_date': datetime.now().date() + timedelta(days=8),
        'guests': 4
    }
]

@app.route('/')
def home():
    """Home page with property dashboard"""
    html = """
<!DOCTYPE html>
<html>
<head>
    <title>Short Term Landlord - Property Management</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: system-ui, sans-serif; background: #f8fafc; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 2rem; text-align: center; }
        .container { max-width: 1200px; margin: 0 auto; padding: 2rem; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); gap: 1.5rem; }
        .card { background: white; border-radius: 12px; padding: 2rem; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        .property-title { font-size: 1.25rem; font-weight: bold; color: #2d3748; margin-bottom: 0.5rem; }
        .property-address { color: #718096; margin-bottom: 1rem; }
        .property-details { display: flex; gap: 1rem; margin-bottom: 1.5rem; }
        .detail-badge { background: #e2e8f0; padding: 0.25rem 0.75rem; border-radius: 16px; font-size: 0.875rem; }
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
        <h1>🏠 Short Term Landlord</h1>
        <p>Complete Property Management Solution</p>
    </div>
    
    <div class="container">
        <h2 style="margin-bottom: 2rem; color: #2d3748;">Property Dashboard</h2>
        
        <div class="grid">
            {% for property in properties %}
            <div class="card">
                <div class="property-title">{{ property.name }}</div>
                <div class="property-address">{{ property.address }}</div>
                
                <div class="property-details">
                    <span class="detail-badge">{{ property.bedrooms }} bed</span>
                    <span class="detail-badge">{{ property.bathrooms }} bath</span>
                    <span class="detail-badge">Check-out: {{ property.checkout_time }}</span>
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
    return render_template_string(html, properties=sample_properties, request=request)

@app.route('/worker-calendar/<token>')
def worker_calendar(token):
    """Worker calendar view"""
    # Find property by token
    property = next((p for p in sample_properties if p['worker_token'] == token), None)
    if not property:
        return jsonify({'error': 'Invalid token'}), 404
    
    # Get bookings for this property
    property_bookings = [b for b in sample_bookings if b['property_id'] == property['id']]
    
    html = """
<!DOCTYPE html>
<html>
<head>
    <title>Worker Calendar - {{ property.name }}</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: system-ui, sans-serif; background: #f8fafc; }
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
            </div>
        </div>
        
        <div class="bookings">
            <h3 style="margin-bottom: 1rem; color: #2d3748;">Upcoming Checkouts</h3>
            
            {% if bookings %}
                {% for booking in bookings %}
                <div class="booking">
                    <div class="booking-header">
                        {{ booking.guest_name }} - Checkout {{ booking.checkout_date.strftime('%B %d, %Y') }}
                    </div>
                    <div class="booking-details">
                        <div>📅 Stay: {{ booking.checkin_date.strftime('%m/%d') }} - {{ booking.checkout_date.strftime('%m/%d') }}</div>
                        <div>👥 Guests: {{ booking.guests }}</div>
                        <div>⏰ Checkout by: <span class="checkout-highlight">{{ property.checkout_time }}</span></div>
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

@app.route('/guest/<int:property_id>/guidebook')
def guest_guidebook(property_id):
    """Guest guidebook view"""
    token = request.args.get('token')
    
    # Find property
    property = next((p for p in sample_properties if p['id'] == property_id), None)
    if not property or property['guest_token'] != token:
        return jsonify({'error': 'Invalid access'}), 403
    
    # Sample guidebook entries
    guidebook_entries = [
        {
            'title': 'Downtown Bistro',
            'category': 'restaurants',
            'description': 'Amazing local cuisine with great steaks and pasta. Perfect for date nights!',
            'address': '789 Food Street',
            'phone': '(555) 123-4567',
            'hours': 'Daily 5PM - 11PM'
        },
        {
            'title': 'City Art Museum',
            'category': 'attractions',
            'description': 'Beautiful collection of local and international art. Free admission on Sundays.',
            'address': '456 Culture Ave',
            'phone': '(555) 987-6543',
            'hours': 'Tue-Sun 10AM - 6PM'
        },
        {
            'title': 'Main Street Market',
            'category': 'shopping',
            'description': 'Local farmers market with fresh produce, crafts, and food trucks.',
            'address': 'Main Street Park',
            'hours': 'Saturdays 8AM - 2PM'
        },
        {
            'title': 'Metro Bus Station',
            'category': 'transportation',
            'description': 'Main bus hub with connections throughout the city. Day passes available.',
            'address': '100 Transit Way',
            'phone': '(555) BUS-RIDE'
        }
    ]
    
    html = """
<!DOCTYPE html>
<html>
<head>
    <title>Guest Guidebook - {{ property.name }}</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: system-ui, sans-serif; background: #f8fafc; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 2rem; text-align: center; }
        .container { max-width: 1000px; margin: 0 auto; padding: 2rem; }
        .welcome { background: white; border-radius: 8px; padding: 2rem; margin-bottom: 2rem; box-shadow: 0 2px 4px rgba(0,0,0,0.1); text-align: center; }
        .categories { display: flex; flex-wrap: wrap; gap: 0.5rem; margin-bottom: 2rem; justify-content: center; }
        .category-btn { background: #e2e8f0; color: #4a5568; padding: 0.5rem 1rem; border: none; border-radius: 20px; cursor: pointer; transition: all 0.2s; }
        .category-btn.active { background: #667eea; color: white; }
        .entries { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1.5rem; }
        .entry { background: white; border-radius: 8px; padding: 1.5rem; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .entry-title { font-weight: bold; color: #2d3748; margin-bottom: 0.5rem; }
        .entry-category { background: #e2e8f0; color: #4a5568; padding: 0.25rem 0.5rem; border-radius: 12px; font-size: 0.8rem; margin-bottom: 0.5rem; display: inline-block; }
        .entry-description { color: #718096; margin-bottom: 1rem; line-height: 1.5; }
        .entry-details { font-size: 0.9rem; color: #4a5568; }
        .entry-details div { margin-bottom: 0.25rem; }
    </style>
</head>
<body>
    <div class="header">
        <h1>📖 Welcome to {{ property.name }}!</h1>
        <p>Your Local Guidebook</p>
    </div>
    
    <div class="container">
        <div class="welcome">
            <h3 style="color: #667eea; margin-bottom: 1rem;">Welcome to Your Stay!</h3>
            <p style="margin-bottom: 1rem;">We've curated some of our favorite local spots for you to explore during your visit.</p>
            <div style="display: flex; justify-content: center; gap: 2rem; font-size: 0.9rem; color: #4a5568;">
                <span><strong>Check-in:</strong> {{ property.checkin_time }}</span>
                <span><strong>Check-out:</strong> {{ property.checkout_time }}</span>
            </div>
        </div>
        
        <div class="categories">
            <button class="category-btn active" onclick="filterEntries('all')">All</button>
            <button class="category-btn" onclick="filterEntries('restaurants')">🍽️ Restaurants</button>
            <button class="category-btn" onclick="filterEntries('attractions')">🎭 Attractions</button>
            <button class="category-btn" onclick="filterEntries('shopping')">🛍️ Shopping</button>
            <button class="category-btn" onclick="filterEntries('transportation')">🚌 Transportation</button>
        </div>
        
        <div class="entries" id="entries">
            {% for entry in entries %}
            <div class="entry" data-category="{{ entry.category }}">
                <div class="entry-title">{{ entry.title }}</div>
                <div class="entry-category">{{ entry.category|title }}</div>
                <div class="entry-description">{{ entry.description }}</div>
                <div class="entry-details">
                    {% if entry.address %}<div>📍 {{ entry.address }}</div>{% endif %}
                    {% if entry.phone %}<div>📞 {{ entry.phone }}</div>{% endif %}
                    {% if entry.hours %}<div>🕒 {{ entry.hours }}</div>{% endif %}
                </div>
            </div>
            {% endfor %}
        </div>
    </div>
    
    <script>
        function filterEntries(category) {
            const entries = document.querySelectorAll('.entry');
            const buttons = document.querySelectorAll('.category-btn');
            
            buttons.forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');
            
            entries.forEach(entry => {
                if (category === 'all' || entry.dataset.category === category) {
                    entry.style.display = 'block';
                } else {
                    entry.style.display = 'none';
                }
            });
        }
    </script>
</body>
</html>
    """
    return render_template_string(html, property=property, entries=guidebook_entries)

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return {
        'status': 'healthy',
        'service': 'short-term-landlord',
        'version': '1.0.0',
        'timestamp': datetime.now().isoformat(),
        'features': [
            'Property Management Dashboard',
            'Worker Calendar Access',
            'Guest Guidebook System',
            'Mobile Responsive Design',
            'Token-based Security'
        ]
    }, 200

@app.route('/service-info')
def service_info():
    """Service information endpoint"""
    return {
        'service_name': 'Short Term Landlord',
        'service_id': 'short-term-landlord',
        'deployment': 'Google App Engine Service',
        'project': os.environ.get('GOOGLE_CLOUD_PROJECT_ID', 'speech-memorization'),
        'version': '1.0.0',
        'status': 'operational',
        'features': {
            'property_dashboard': True,
            'worker_calendar': True,
            'guest_guidebook': True,
            'token_security': True,
            'mobile_responsive': True,
            'demo_data': True
        },
        'demo_links': {
            'worker_calendar': f"{request.host_url}worker-calendar/demo-worker-token-123",
            'guest_guidebook': f"{request.host_url}guest/1/guidebook?token=demo-guest-token-123"
        },
        'sample_properties': len(sample_properties),
        'sample_bookings': len(sample_bookings)
    }

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)