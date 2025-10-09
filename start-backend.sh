#!/bin/bash
# Start backend server with environment variables loaded

cd "$(dirname "$0")/backend"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}🚀 Starting Workspace Guardian Backend...${NC}"
echo ""

# Check if venv exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}❌ Virtual environment not found. Run ./setup-python313.sh first${NC}"
    exit 1
fi

# Activate venv
source venv/bin/activate

# Load environment variables
if [ ! -f "../.env" ]; then
    echo -e "${YELLOW}❌ .env file not found. Please create it from env.template${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Loading environment variables from .env${NC}"
export $(cat ../.env | grep -v '^#' | xargs)

# Verify critical env vars
if [ -z "$DATABRICKS_HOST" ] || [ -z "$DATABRICKS_TOKEN" ]; then
    echo -e "${YELLOW}❌ DATABRICKS_HOST or DATABRICKS_TOKEN not set in .env${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Databricks Host: $DATABRICKS_HOST${NC}"
echo -e "${GREEN}✅ Starting server on http://localhost:8000${NC}"
echo ""
echo "Press CTRL+C to stop the server"
echo ""

# Start uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000



