#!/bin/bash
set -e

# Preserve templates directory
echo "Ensuring template directories exist..."
mkdir -p /app/app/templates/custom

# Simple database initialization
echo "Setting up database..."

# Initialize migrations if needed
if [ ! -d 'migrations' ] || [ ! -f 'migrations/env.py' ]; then
  echo "Initializing database migrations..."
  flask db init
fi

# Create database tables if they don't exist
echo "Creating database tables if needed..."
python /app/reset_db.py || true

# Fix PostgreSQL schema issues
echo "Fixing PostgreSQL schema issues..."
python /app/fix_postgres_schema.py || true

echo "Starting web server..."
exec flask run --host=0.0.0.0 