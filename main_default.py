"""
Default service for serverless-test-12345 project
Minimal service required before deploying Short Term Landlord
"""

from flask import Flask

app = Flask(__name__)

@app.route('/')
def index():
    return """
    <h1>Serverless Project Default Service</h1>
    <p>Project: serverless-test-12345</p>
    <p>This is the default service. Short Term Landlord app is available at:</p>
    <p><a href="https://short-term-landlord-dot-serverless-test-12345.uc.r.appspot.com">Short Term Landlord Service</a></p>
    """

@app.route('/health')
def health():
    return {'status': 'healthy', 'service': 'default'}

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080)