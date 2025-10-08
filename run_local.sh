#!/bin/bash
# Quick start script for local development

export FLASK_APP=main.py
export FLASK_ENV=development

# Activate virtual environment
source venv/bin/activate

# Start Flask development server
echo "🚀 Starting Short Term Landlord local development server..."
echo "📱 Admin login: admin@localhost.com / admin123"
echo "🌐 URL: http://localhost:5001"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

flask run --host=0.0.0.0 --port=5001 --debug