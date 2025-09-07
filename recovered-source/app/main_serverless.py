"""
Short Term Landlord - Serverless Deployment
Complete property management application for serverless-test-12345 project
"""

import os
import logging
from flask import Flask, render_template_string, redirect, url_for

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'serverless-landlord-key')

# Configure logging
logging.basicConfig(level=logging.INFO)
app.logger.setLevel(logging.INFO)

# Global variables to track application status
app_status = {
    'full_app_loaded': False,
    'models_available': False,
    'database_initialized': False,
    'error_message': None
}

try:
    # Try to load the complete application
    from app import create_app, db
    from config import config
    
    # Create the full application
    config_name = os.environ.get('FLASK_ENV', 'appengine') 
    if config_name in config:
        app = create_app(config[config_name])
    else:
        app = create_app(config['appengine'])
    
    app.logger.info("✅ Full Short Term Landlord application loaded successfully")
    app_status['full_app_loaded'] = True
    
    # Configure for serverless deployment
    app.config.update({
        'GOOGLE_CLOUD_PROJECT_ID': 'serverless-test-12345',
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False,
        'NOTIFICATION_EMAIL_ENABLED': False,
        'NOTIFICATION_SMS_ENABLED': False,
    })
    
    # Initialize database
    with app.app_context():
        try:
            db.create_all()
            app.logger.info("✅ Database tables created")
            app_status['database_initialized'] = True
        except Exception as db_error:
            app.logger.error(f"Database initialization error: {db_error}")
            app_status['error_message'] = str(db_error)

    # Check if models are available
    try:
        from app.models import User, Property
        app_status['models_available'] = True
        app.logger.info("✅ Models imported successfully")
    except Exception as model_error:
        app.logger.error(f"Model import error: {model_error}")
        app_status['error_message'] = str(model_error)

except Exception as e:
    app.logger.error(f"❌ Failed to load full application: {str(e)}")
    app_status['error_message'] = str(e)
    
    # Create fallback Flask app if full app fails
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'serverless-landlord-fallback')

# Root route that shows application status
@app.route('/')
def index():
    """Main entry point showing application status"""
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Short Term Landlord - Serverless Deployment</title>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; background: #f8fafc; }
            .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 2rem; text-align: center; }
            .container { max-width: 1200px; margin: 0 auto; padding: 2rem; }
            .card { background: white; padding: 1.5rem; margin: 1rem 0; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
            .btn { display: inline-block; background: #667eea; color: white; padding: 0.75rem 1.5rem; text-decoration: none; border-radius: 8px; margin: 0.5rem; }
            .success { color: #38a169; }
            .error { color: #e53e3e; }
            .status { padding: 1rem; border-radius: 8px; margin: 1rem 0; }
            .status.success { background: #f0fff4; border: 1px solid #68d391; }
            .status.error { background: #fed7d7; border: 1px solid #fc8181; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🏠 Short Term Landlord</h1>
            <p>Property Management System</p>
            <p><strong>Serverless Project:</strong> serverless-test-12345</p>
        </div>
        
        <div class="container">
            <div class="card">
                <h2>🚀 Deployment Status</h2>
                
                <div class="status {{ 'success' if app_status['full_app_loaded'] else 'error' }}">
                    <strong>Full Application:</strong> 
                    {{ '✅ Loaded' if app_status['full_app_loaded'] else '❌ Failed to load' }}
                </div>
                
                <div class="status {{ 'success' if app_status['models_available'] else 'error' }}">
                    <strong>Database Models:</strong> 
                    {{ '✅ Available' if app_status['models_available'] else '❌ Not available' }}
                </div>
                
                <div class="status {{ 'success' if app_status['database_initialized'] else 'error' }}">
                    <strong>Database:</strong> 
                    {{ '✅ Initialized' if app_status['database_initialized'] else '❌ Not initialized' }}
                </div>
                
                {% if app_status['error_message'] %}
                <div class="status error">
                    <strong>Error:</strong> {{ app_status['error_message'] }}
                </div>
                {% endif %}
            </div>
            
            <div class="card">
                <h2>🏠 Property Management Access</h2>
                {% if app_status['full_app_loaded'] %}
                <p>Your complete property management system is available:</p>
                <a href="/property-access" class="btn">🏠 Access Property Management</a>
                <a href="/create-sample-data" class="btn">📝 Create Sample Data</a>
                <a href="/system-info" class="btn">🔧 System Information</a>
                {% else %}
                <p>Full application not loaded. Basic functionality available:</p>
                <a href="/basic-info" class="btn">ℹ️ Basic System Info</a>
                <a href="/debug-deployment" class="btn">🔧 Debug Deployment</a>
                {% endif %}
            </div>
        </div>
    </body>
    </html>
    """, app_status=app_status)

@app.route('/property-access')
def property_access():
    """Access property management features"""
    if not app_status['models_available']:
        return redirect(url_for('index'))
    
    try:
        from app.models import Property, User
        
        # Get property and user counts
        property_count = Property.query.count()
        user_count = User.query.count()
        
        return render_template_string("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Property Management - Short Term Landlord</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; background: #f4f4f4; }
                .container { max-width: 1000px; margin: 0 auto; }
                .header { background: #2c3e50; color: white; padding: 20px; border-radius: 8px; text-align: center; }
                .card { background: white; padding: 20px; margin: 20px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                .btn { display: inline-block; background: #3498db; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px; margin: 5px; }
                .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; }
                .stat { background: #ecf0f1; padding: 15px; border-radius: 8px; text-align: center; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🏠 Property Management Dashboard</h1>
                    <p>Complete property management system deployed to serverless-test-12345</p>
                </div>
                
                <div class="card">
                    <h2>📊 Current Statistics</h2>
                    <div class="stats">
                        <div class="stat">
                            <h3>{{ property_count }}</h3>
                            <p>Properties</p>
                        </div>
                        <div class="stat">
                            <h3>{{ user_count }}</h3>
                            <p>Users</p>
                        </div>
                        <div class="stat">
                            <h3>Active</h3>
                            <p>System Status</p>
                        </div>
                    </div>
                </div>
                
                <div class="card">
                    <h2>🚀 Available Features</h2>
                    <p>Your complete Short Term Landlord application includes:</p>
                    <a href="/property" class="btn">🏠 Property Management</a>
                    <a href="/auth" class="btn">👤 User Authentication</a>
                    <a href="/calendar" class="btn">📅 Calendar System</a>
                    <a href="/admin" class="btn">⚙️ Admin Panel</a>
                    <a href="/tasks" class="btn">📋 Task Management</a>
                    <a href="/workforce" class="btn">👥 Workforce</a>
                    <a href="/guidebook" class="btn">📖 Guidebooks</a>
                    <a href="/inventory" class="btn">📦 Inventory</a>
                </div>
                
                <div class="card">
                    <h2>🔧 System Tools</h2>
                    <a href="/create-sample-data" class="btn">📝 Create Sample Data</a>
                    <a href="/system-info" class="btn">ℹ️ System Information</a>
                    <a href="/" class="btn">🏠 Back to Home</a>
                </div>
            </div>
        </body>
        </html>
        """, property_count=property_count, user_count=user_count)
        
    except Exception as e:
        return f'<h1>Property Access Error</h1><p>{str(e)}</p><p><a href="/">Back to Home</a></p>'

@app.route('/create-sample-data')
def create_sample_data():
    """Create sample properties and users for testing"""
    if not app_status['models_available']:
        return redirect(url_for('index'))
    
    try:
        from app.models import Property, User
        from app import db
        
        # Create admin user if doesn't exist
        admin = User.query.filter_by(email='admin@landlord.com').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@landlord.com',
                first_name='Admin',
                last_name='User'
            )
            if hasattr(admin, 'set_password'):
                admin.set_password('admin123')
            db.session.add(admin)
            db.session.flush()
        
        # Create sample properties
        sample_properties = [
            {
                'name': 'Oceanview Condo',
                'address': '123 Beach Blvd, Miami, FL 33139',
                'description': 'Beautiful oceanview condominium with private balcony'
            },
            {
                'name': 'Mountain Lodge',
                'address': '456 Alpine Drive, Denver, CO 80424',
                'description': 'Rustic mountain lodge with ski-in/ski-out access'
            },
            {
                'name': 'City Loft',
                'address': '789 Urban Street, New York, NY 10001',
                'description': 'Modern downtown loft with city skyline views'
            }
        ]
        
        created_count = 0
        for sample in sample_properties:
            existing = Property.query.filter_by(name=sample['name']).first()
            if not existing:
                new_property = Property(
                    name=sample['name'],
                    address=sample['address'],
                    description=sample['description'],
                    owner_id=admin.id
                )
                db.session.add(new_property)
                created_count += 1
        
        db.session.commit()
        
        return f"""
        <h1>✅ Sample Data Created!</h1>
        <p>Created {created_count} new properties.</p>
        <p>Admin user: admin@landlord.com (password: admin123)</p>
        <p><a href="/property-access">View Property Management</a></p>
        <p><a href="/">Back to Home</a></p>
        """
        
    except Exception as e:
        return f'<h1>Sample Data Creation Error</h1><p>{str(e)}</p>'

@app.route('/system-info')
def system_info():
    """Show detailed system information"""
    try:
        info = {
            'project': 'serverless-test-12345',
            'app_name': app.name,
            'total_routes': len(app.url_map._rules),
            'blueprints': list(app.blueprints.keys()) if hasattr(app, 'blueprints') else [],
            'config_keys': list(app.config.keys())[:10],  # First 10 config keys
        }
        
        if app_status['models_available']:
            try:
                from app import models
                model_classes = [name for name in dir(models) 
                               if hasattr(getattr(models, name), '__tablename__')]
                info['models'] = model_classes[:10]  # First 10 models
            except:
                info['models'] = ['Error loading models']
        
        return f"""
        <h1>🔧 System Information</h1>
        <h2>Project: {info['project']}</h2>
        <p><strong>App Name:</strong> {info['app_name']}</p>
        <p><strong>Total Routes:</strong> {info['total_routes']}</p>
        <p><strong>Blueprints:</strong> {', '.join(info['blueprints'])}</p>
        <p><strong>Models Available:</strong> {', '.join(info.get('models', ['None']))}</p>
        <p><strong>Config Keys:</strong> {', '.join(info['config_keys'])}</p>
        <p><a href="/">Back to Home</a></p>
        """
        
    except Exception as e:
        return f'<h1>System Info Error</h1><p>{str(e)}</p>'

@app.route('/health')
def health():
    """Health check endpoint"""
    return {
        'status': 'healthy',
        'service': 'short-term-landlord',
        'project': 'serverless-test-12345',
        'full_app_loaded': app_status['full_app_loaded']
    }

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)