#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Get script directory and project root directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." &> /dev/null && pwd )"

echo -e "${GREEN}Installing required Python packages...${NC}"

# Check if we're in a virtual environment
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo -e "${YELLOW}Warning: Not running in a virtual environment${NC}"
    echo -e "${YELLOW}It's recommended to activate a virtual environment first${NC}"
    
    # Ask if user wants to proceed
    read -p "Do you want to continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${RED}Installation aborted.${NC}"
        exit 1
    fi
fi

# Check if requirements.txt exists in the script directory
REQUIREMENTS_FILE=""
if [ -f "${SCRIPT_DIR}/requirements.txt" ]; then
    REQUIREMENTS_FILE="${SCRIPT_DIR}/requirements.txt"
# Check if requirements.txt exists in the project root
elif [ -f "${PROJECT_ROOT}/requirements.txt" ]; then
    REQUIREMENTS_FILE="${PROJECT_ROOT}/requirements.txt"
else
    echo -e "${RED}Error: requirements.txt not found${NC}"
    exit 1
fi

# Install packages
echo -e "${GREEN}Installing packages from ${REQUIREMENTS_FILE}...${NC}"
python3 -m pip install -r "${REQUIREMENTS_FILE}"

if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Failed to install some packages${NC}"
    exit 1
else
    echo -e "${GREEN}All packages installed successfully!${NC}"
    exit 0
fi 