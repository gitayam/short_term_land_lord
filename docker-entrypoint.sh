#!/bin/bash
set -e

# Preserve templates directory
echo "Ensuring template directories exist..."
mkdir -p /app/app/templates/custom

# Create migrations directory if it doesn't exist
echo "Ensuring migrations directory exists..."
mkdir -p /app/migrations

# In Docker, we'll directly run the database initialization instead of using the script
echo "Running database preparation directly..."

# Initialize migrations if needed
if [ ! -d 'migrations/versions' ] || [ ! -f 'migrations/env.py' ]; then
  echo "Initializing database migrations..."
  flask db init
fi

# Apply migrations
echo "Applying database migrations..."
flask db upgrade || echo "WARNING: Database migrations failed but continuing..."

# Run a simple database check
echo "Verifying database setup..."
python3 -c "
import os, sys
from flask import Flask
from sqlalchemy import inspect

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'postgresql://postgres:postgres@db/flask_app')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

from app import db
db.init_app(app)

with app.app_context():
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    print(f'Found tables: {\", \".join(tables) if tables else \"No tables\"}')
    
    # Create tables if none exist (fallback)
    if not tables:
        print('No tables found. Creating tables directly...')
        from app.models import User, Property, Task, SiteSettings
        db.create_all()
        print('Tables created directly.')
" || echo "WARNING: Database verification failed but continuing..."

# Create admin user if it doesn't exist using the create_admin.py script
echo "Ensuring admin user exists using environment variables..."
python3 create_admin.py || echo "WARNING: Admin user creation failed but continuing..."

echo "Starting web server..."
exec flask run --host=0.0.0.0 