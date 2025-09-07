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

# Parse command line arguments
RESET=false
FORCE_FIXES=false

while [[ "$#" -gt 0 ]]; do
    case $1 in
        --reset) RESET=true ;;
        --force-fixes) FORCE_FIXES=true ;;
        --help) 
            echo "Usage: $0 [options]"
            echo "Options:"
            echo "  --reset        Reset the database before running migrations"
            echo "  --force-fixes  Force all database fixes to run even if no migrations were applied"
            echo "  --help         Show this help message"
            exit 0
            ;;
        *) echo "Unknown parameter: $1"; exit 1 ;;
    esac
    shift
done

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

# Build the command with appropriate flags
CMD="python migrations/run_all_migrations.py"
if [ "$RESET" = true ]; then
    echo -e "${YELLOW}Database reset requested. This will delete all data!${NC}"
    CMD="$CMD --reset"
fi

if [ "$FORCE_FIXES" = true ]; then
    echo -e "${BLUE}Force fixes mode enabled. All database fixes will run.${NC}"
    CMD="$CMD --force-fixes"
fi

# Run the unified migration script with arguments
echo -e "${BLUE}Running migrations with command: $CMD${NC}"
eval $CMD

# Check if the migration script was successful
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ All migrations completed successfully!${NC}"
else
    echo -e "${RED}❌ Migrations encountered errors. Check the logs for details.${NC}"
    echo -e "${YELLOW}Attempting to run consolidated_db_fixes.py as a fallback...${NC}"
    
    # Run consolidated_db_fixes.py as a fallback
    python migrations/consolidated_db_fixes.py
    
    if [ $? -eq 0 ]; then
        echo -e "${YELLOW}⚠️ Fallback fixes completed. The system may work with limitations.${NC}"
    else
        echo -e "${RED}❌ Both migration approaches failed. Database may not be properly configured.${NC}"
        exit 1
    fi
fi

# Final check to ensure admin user exists
echo -e "${BLUE}Verifying admin user exists...${NC}"
python migrations/check_admin.py

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Admin user verified.${NC}"
else
    echo -e "${YELLOW}⚠️ Admin user check failed. Creating admin user...${NC}"
    python migrations/create_admin.py
fi

echo -e "${GREEN}Database migration process complete. Application is ready to start.${NC}"
exit 0 