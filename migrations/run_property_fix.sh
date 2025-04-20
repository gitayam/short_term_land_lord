#!/bin/bash
# Run the property details migration and ensure the admin is created properly from .env

# Make the script exit if any command fails
set -e

echo "Starting property fix and admin user update..."

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
elif [ -d "env" ]; then
    echo "Activating virtual environment..."
    source env/bin/activate
fi

# Ensure requirements are installed
echo "Installing required packages..."
pip install -r requirements.txt

# Run the property detail fields migration
echo "Running property details migration..."
python migrations/add_property_details.py

# Ensure admin user is created/updated properly
echo "Creating/updating admin user from .env..."
python migrations/create_admin.py

echo "Property fix and admin user update completed successfully!" 