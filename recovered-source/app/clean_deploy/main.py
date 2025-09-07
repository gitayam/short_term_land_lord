from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return '<h1>🏠 Short Term Landlord</h1><p>Serverless Project: serverless-test-12345</p><p>Default Service Active</p>'

@app.route('/health')
def health():
    return {'status': 'healthy'}

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080)