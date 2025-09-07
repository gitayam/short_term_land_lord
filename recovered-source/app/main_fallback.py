"""
Fallback version - minimal Flask app for App Engine deployment
"""
import os
from flask import Flask, jsonify

# Create the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'fallback-secret-key')

@app.route('/')
def home():
    """Home page showing deployment status"""
    return {
        'status': 'success',
        'message': 'Short Term Landlord App is running on Google App Engine!',
        'service': 'short-term-landlord',
        'version': '1.0.0',
        'features': [
            'Interactive Guest Guidebooks',
            'Worker Calendar Access', 
            'Property Management',
            'Task Assignment',
            'Inventory Tracking'
        ],
        'note': 'Full application features available after database setup'
    }

@app.route('/health')
def health_check():
    """Health check endpoint for App Engine"""
    return {
        'status': 'healthy',
        'service': 'short-term-landlord',
        'version': '1.0.0'
    }, 200

@app.route('/status')
def status():
    """Detailed status endpoint"""
    return {
        'application': 'Short Term Landlord',
        'deployment': 'Google App Engine',
        'runtime': 'Python 3.11',
        'status': 'operational',
        'endpoints': {
            '/': 'Home page',
            '/health': 'Health check',
            '/status': 'This status page'
        }
    }

if __name__ == '__main__':
    # This is used only for local development
    app.run(host='127.0.0.1', port=8080, debug=True)