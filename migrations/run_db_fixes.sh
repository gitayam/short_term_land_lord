#!/bin/bash
# Database preparation and fix script
# This script ensures all necessary database fixes are applied

set -e

# Set colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get script directory for relative paths
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Check if we're running in Docker
ENVIRONMENT=$1
if [ -z "$ENVIRONMENT" ]; then
    # Try to detect environment
    if [ -f /.dockerenv ]; then
        ENVIRONMENT="docker"
    else
        ENVIRONMENT="local"
    fi
fi

echo -e "${BLUE}Starting database fixes in ${ENVIRONMENT} environment...${NC}"

# Function to check and install Python requirements
check_requirements() {
    echo -e "${BLUE}Checking Python requirements...${NC}"
    
    # Skip requirements check in Docker environment
    if [ "$ENVIRONMENT" == "docker" ]; then
        echo -e "${YELLOW}Running in Docker environment, skipping requirements check.${NC}"
        return 0
    fi
    
    # Check if install_requirements.sh exists and is executable
    if [ -f "${SCRIPT_DIR}/install_requirements.sh" ]; then
        chmod +x "${SCRIPT_DIR}/install_requirements.sh"
        "${SCRIPT_DIR}/install_requirements.sh"
        
        if [ $? -ne 0 ]; then
            echo -e "${RED}❌ Failed to install required Python packages.${NC}"
            return 1
        else
            echo -e "${GREEN}✓ Python requirements satisfied.${NC}"
            return 0
        fi
    else
        echo -e "${YELLOW}⚠️ install_requirements.sh not found. Skipping requirements check.${NC}"
        echo -e "${YELLOW}Make sure all required packages are installed.${NC}"
        return 0
    fi
}

# Function to run startup.py for transaction fixes
run_startup() {
    echo -e "${BLUE}Running startup script for transaction fixes...${NC}"
    
    if [ "$ENVIRONMENT" == "docker" ]; then
        python3 "${SCRIPT_DIR}/startup.py"
    else
        python3 "${SCRIPT_DIR}/startup.py"
    fi
    
    if [ $? -ne 0 ]; then
        echo -e "${YELLOW}⚠️ Warning: Transaction fixes script returned non-zero exit code.${NC}"
        echo -e "${YELLOW}Continuing anyway, but there might be issues later.${NC}"
    else
        echo -e "${GREEN}✓ Transaction fixes completed successfully.${NC}"
    fi
}

# Function to run migrations
run_migrations() {
    echo -e "${BLUE}Running database migrations...${NC}"
    
    # Initialize migrations if needed
    if [ ! -d "migrations" ]; then
        echo -e "${YELLOW}Migrations directory not found. Initializing...${NC}"
        flask db init
        if [ $? -ne 0 ]; then
            echo -e "${RED}❌ Failed to initialize migrations.${NC}"
            return 1
        fi
    fi
    
    # Generate migration script if needed
    if [ ! -f "migrations/versions/*.py" ]; then
        echo -e "${YELLOW}No migration versions found. Generating...${NC}"
        flask db migrate -m "Initial migration"
        if [ $? -ne 0 ]; then
            echo -e "${RED}❌ Failed to generate migration script.${NC}"
            return 1
        fi
    fi
    
    # Apply migrations
    echo -e "${BLUE}Applying migrations...${NC}"
    flask db upgrade
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Failed to apply migrations.${NC}"
        return 1
    else
        echo -e "${GREEN}✓ Database migrations applied successfully.${NC}"
        return 0
    fi
}

# Function to create database tables directly if migrations fail
create_tables_directly() {
    echo -e "${YELLOW}⚠️ Migrations failed. Attempting direct table creation...${NC}"
    
    python3 "${SCRIPT_DIR}/reset_db.py"
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Failed to create tables directly.${NC}"
        return 1
    else
        echo -e "${GREEN}✓ Tables created directly successfully.${NC}"
        return 0
    fi
}

# Function to run all database fixes
run_db_fixes() {
    # 0. Check requirements
    check_requirements
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Requirements check failed. Fix package installation issues before proceeding.${NC}"
        return 1
    fi
    
    # 1. Run startup.py to fix transactions
    run_startup
    
    # 2. Run migrations (or direct table creation if migrations fail)
    run_migrations
    migration_status=$?
    
    if [ $migration_status -ne 0 ]; then
        echo -e "${YELLOW}Migrations failed. Trying direct table creation.${NC}"
        create_tables_directly
        direct_status=$?
        
        if [ $direct_status -ne 0 ]; then
            echo -e "${RED}❌ All database preparation methods failed. Application may not start correctly.${NC}"
            return 1
        fi
    fi
    
    # 3. Verify database is ready
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
    critical_tables = ['users', 'site_settings', 'registration_requests']
    missing = [t for t in critical_tables if t not in tables]
    
    if missing:
        print(f'Missing tables: {", ".join(missing)}')
        sys.exit(1)
    else:
        print('All critical tables exist.')
        sys.exit(0)
"
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Database verification failed. Critical tables are missing.${NC}"
        return 1
    else
        echo -e "${GREEN}✓ Database verification successful. All tables exist.${NC}"
    fi
    
    echo -e "${GREEN}✓ All database fixes completed successfully.${NC}"
    return 0
}

# Run all fixes
run_db_fixes

exit_code=$?
if [ $exit_code -ne 0 ]; then
    echo -e "${RED}❌ Database fixes encountered errors.${NC}"
    exit $exit_code
else
    echo -e "${GREEN}✓ Database is ready for application startup.${NC}"
    exit 0
fi