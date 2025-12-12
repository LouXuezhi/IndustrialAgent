#!/bin/bash
# Quick test runner script for Industrial QA Backend

set -e

echo "=========================================="
echo "Industrial QA Backend - Test Runner"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if server is running
echo -e "${YELLOW}Checking if server is running...${NC}"
if curl -s http://localhost:8000/ > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Server is running${NC}"
else
    echo -e "${RED}✗ Server is not running${NC}"
    echo "Please start the server first:"
    echo "  uvicorn app.main:app --reload"
    exit 1
fi

# Step 1: Initialize test data
echo ""
echo -e "${YELLOW}Step 1: Initializing test data...${NC}"
if uv run python tests/init_test_data.py; then
    echo -e "${GREEN}✓ Test data initialized${NC}"
else
    echo -e "${RED}✗ Failed to initialize test data${NC}"
    exit 1
fi

# Step 2: Run API tests
echo ""
echo -e "${YELLOW}Step 2: Running API endpoint tests...${NC}"
if uv run python tests/test_api_endpoints.py; then
    echo ""
    echo -e "${GREEN}=========================================="
    echo "All tests completed successfully!"
    echo "==========================================${NC}"
    exit 0
else
    echo ""
    echo -e "${RED}=========================================="
    echo "Some tests failed. Please check the output above."
    echo "==========================================${NC}"
    exit 1
fi

