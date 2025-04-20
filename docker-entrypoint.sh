#!/bin/bash
set -e

# Preserve templates directory
echo "Ensuring template directories exist..."
mkdir -p /app/app/templates/custom

# Run our comprehensive database preparation and fix script
echo "Running database preparation and fixes..."
bash /app/run_db_fixes.sh

# Initialize migrations if needed
if [ ! -d 'migrations' ] || [ ! -f 'migrations/env.py' ]; then
  echo "Initializing database migrations..."
  flask db init
fi

echo "Starting web server..."
exec flask run --host=0.0.0.0 