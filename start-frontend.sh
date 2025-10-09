#!/bin/bash
# Start frontend development server

cd "$(dirname "$0")/frontend"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}🎨 Starting Workspace Guardian Frontend...${NC}"
echo ""

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}❌ node_modules not found. Run npm install first${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Starting Vite dev server${NC}"
echo -e "${GREEN}✅ Frontend will be available at http://localhost:3000${NC}"
echo ""
echo "Press CTRL+C to stop the server"
echo ""

# Start npm dev server
npm run dev



