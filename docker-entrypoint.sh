#!/bin/bash
# Docker entrypoint script to ensure all migrations run before starting the Flask app
set -e

# Setup colors for better output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to handle failures gracefully
handle_failure() {
    echo -e "${RED}Critical error: $1${NC}"
    echo -e "${YELLOW}Sleeping for 30 seconds before exiting to prevent rapid container restarts...${NC}"
    sleep 30
    exit 1
}

echo -e "${BLUE}Starting database initialization and migrations...${NC}"

# Wait for the database to be ready
python -c "
import time
import socket
import sys

port = 5432
host = 'db'
max_attempts = 30
attempts = 0

print(f'Waiting for PostgreSQL at {host}:{port}...')
while attempts < max_attempts:
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        sock.connect((host, port))
        sock.close()
        print('PostgreSQL is available!')
        sys.exit(0)  # Exit successfully when connection succeeds
    except Exception as e:
        attempts += 1
        print(f'PostgreSQL not available yet. Retry {attempts}/{max_attempts}...')
        time.sleep(1)

# Only reached if all attempts failed
print('Could not connect to PostgreSQL. Exiting.')
sys.exit(1)
"

# Check if the PostgreSQL connection was successful
if [ $? -ne 0 ]; then
    handle_failure "Failed to connect to PostgreSQL database. Cannot continue."
fi

echo -e "${GREEN}Successfully connected to PostgreSQL.${NC}"

# Run the simplified database bootstrapping script
echo -e "${BLUE}Running simplified database bootstrap script...${NC}"
python /app/migrations/db_bootstrap.py

if [ $? -ne 0 ]; then
    echo -e "${RED}Database bootstrap script failed. This may cause issues with the application.${NC}"
    echo -e "${YELLOW}Continuing anyway...${NC}"
else
    echo -e "${GREEN}Database bootstrap completed successfully!${NC}"
fi

# Run site settings and other fixes
echo -e "${BLUE}Running database fixes...${NC}"
python migrations/consolidated_db_fixes.py || true

# Start the Flask application
echo -e "${GREEN}Database is ready. Starting Flask application...${NC}"
exec "$@" 