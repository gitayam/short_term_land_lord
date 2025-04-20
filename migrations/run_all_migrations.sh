#!/bin/bash
# Consolidated script to run all migrations in the correct order
# This script is the main entry point for all database migrations and fixes

# Make the script exit if any command fails
set -e

# Setup colors for better output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Starting comprehensive database migrations and fixes...${NC}"

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo -e "${BLUE}Activating virtual environment (venv)...${NC}"
    source venv/bin/activate
elif [ -d "env" ]; then
    echo -e "${BLUE}Activating virtual environment (env)...${NC}"
    source env/bin/activate
fi

# Ensure requirements are installed
echo -e "${BLUE}Installing required packages...${NC}"
pip install -r requirements.txt

# Run the unified migration script
echo -e "${BLUE}Running all migrations...${NC}"
python migrations/run_all_migrations.py

# Check if the migration script was successful
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ All migrations completed successfully!${NC}"
else
    echo -e "${RED}❌ Migrations encountered errors. Check the logs for details.${NC}"
    echo -e "${YELLOW}Attempting to run startup.py as fallback...${NC}"
    
    # Run startup.py as a fallback
    python migrations/startup.py
    
    if [ $? -eq 0 ]; then
        echo -e "${YELLOW}⚠️ Startup script completed with potential issues. The system may work with limitations.${NC}"
    else
        echo -e "${RED}❌ Both migration approaches failed. Database may not be properly configured.${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}Database migration process complete. Application is ready to start.${NC}"
exit 0 