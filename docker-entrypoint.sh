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

# Create admin user if it doesn't exist
echo "Ensuring admin user exists..."
python3 -c "
import os
from app import create_app, db
from app.models import User, UserRoles

app = create_app()
with app.app_context():
    # Check if admin user exists
    admin = User.query.filter_by(email='admin@example.com').first()
    
    if not admin:
        # Create new admin user
        admin = User(
            username='admin',
            email='admin@example.com',
            first_name='Admin',
            last_name='User',
            role=UserRoles.ADMIN.value,
            _is_admin=True
        )
        admin.set_password('adminpass')
        db.session.add(admin)
        db.session.commit()
        print('Admin user created successfully')
    else:
        # Update admin role and password if admin exists
        admin.role = UserRoles.ADMIN.value
        admin._is_admin = True
        admin.set_password('adminpass')
        db.session.commit()
        print('Admin user updated successfully')
" || echo "WARNING: Admin user creation failed but continuing..."

echo "Starting web server..."
exec flask run --host=0.0.0.0 