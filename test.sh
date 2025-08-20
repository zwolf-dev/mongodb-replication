#!/bin/bash

echo "Testing Book Management System..."

# Base URL
BASE_URL="http://localhost:3000"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Test connection
echo -n "Testing server connection... "
if curl -s -o /dev/null -w "%{http_code}" $BASE_URL | grep -q "200"; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
    exit 1
fi

# Test adding a book
echo -n "Testing book creation... "
RESPONSE=$(curl -s -X POST $BASE_URL/add \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "title=Test Book&author=Test Author&year=2024&isbn=1234567890" \
  -w "%{http_code}" \
  -o /dev/null)

if [ "$RESPONSE" = "302" ]; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
fi

# Test search functionality
echo -n "Testing search... "
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/search?query=Test")
if [ "$RESPONSE" = "200" ]; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
fi

echo "All tests completed!"
