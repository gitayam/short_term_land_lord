#!/bin/bash
# Cloud Run entrypoint script - simplified for SQLite
set -e

echo "🏠 Starting Short Term Landlord for Cloud Run..."
echo "Using SQLite database at /tmp/app.db"

# Set up environment for Cloud Run
export FLASK_APP=main.py
export PYTHONPATH=/app:$PYTHONPATH
export PORT=${PORT:-8080}

echo "🚀 Starting Flask application on port $PORT..."

# Start the Flask app with gunicorn directly, let the app create the database
exec gunicorn main:app --bind 0.0.0.0:$PORT --workers 1 --threads 8 --timeout 0