"""
Short Term Landlord - Basic Serverless Deployment
"""

import os
from flask import Flask

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'basic-key')

@app.route('/')
def index():
    return """
    <h1>🏠 Short Term Landlord</h1>
    <p>Project: serverless-test-12345</p>
    <p>Status: ✅ Basic service running</p>
    <p><a href="/health">Health Check</a></p>
    """

@app.route('/health')
def health():
    return {'status': 'healthy', 'project': 'serverless-test-12345'}

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080)