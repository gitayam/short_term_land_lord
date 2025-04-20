#!/bin/bash
# Database preparation and fix script
# This script ensures all necessary database fixes are applied

set -e

# Print with color
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting database preparation and fixes...${NC}"

# Determine environment (test or production)
if [ "$1" == "test" ]; then
  echo -e "${YELLOW}Preparing database for test environment...${NC}"
  python3 prepare_db_for_tests.py
else
  echo -e "${YELLOW}Preparing database for production environment...${NC}"
  python3 startup.py
fi

# Check if the database preparation script succeeded
if [ $? -ne 0 ]; then
  echo -e "${RED}⚠️ WARNING: Database preparation encountered issues${NC}"
  echo -e "${YELLOW}Continuing with additional fixes...${NC}"
fi

# Run additional fix scripts
echo -e "${YELLOW}Applying additional database fixes...${NC}"

# Create database tables if they don't exist
echo -e "${YELLOW}Creating database tables if needed...${NC}"
python3 reset_db.py || echo -e "${RED}⚠️ Reset DB failed, but continuing...${NC}"

# Fix PostgreSQL schema issues
echo -e "${YELLOW}Fixing PostgreSQL schema issues...${NC}"
python3 fix_postgres_schema.py || echo -e "${RED}⚠️ Schema fix failed, but continuing...${NC}"

# Fix admin role issues
if [ -f scripts/fix_admin_role.py ]; then
  echo -e "${YELLOW}Checking and fixing admin role issues...${NC}"
  python3 scripts/fix_admin_role.py || echo -e "${RED}⚠️ Admin role fix failed, but continuing...${NC}"
fi

echo -e "${GREEN}Database preparation and fixes completed!${NC}"
echo -e "${GREEN}You can now start the application or run tests.${NC}"