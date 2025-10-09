#!/bin/bash
set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🚀 Starting Workspace Guardian Development Environment${NC}"
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  .env file not found. Creating from template...${NC}"
    cp env.template .env
    echo -e "${YELLOW}⚠️  Please edit .env with your Databricks credentials${NC}"
    exit 1
fi

# Function to check if port is in use
check_port() {
    lsof -i :$1 &> /dev/null
    return $?
}

# Check ports
if check_port 8000; then
    echo -e "${YELLOW}⚠️  Port 8000 is already in use. Stop the existing process or change the port.${NC}"
    exit 1
fi

if check_port 3000; then
    echo -e "${YELLOW}⚠️  Port 3000 is already in use. Stop the existing process or change the port.${NC}"
    exit 1
fi

# Function to cleanup on exit
cleanup() {
    echo ""
    echo -e "${YELLOW}Shutting down services...${NC}"
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit 0
}

trap cleanup SIGINT SIGTERM

# Start backend
echo -e "${GREEN}📦 Starting backend on port 8000...${NC}"
cd backend

if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Virtual environment not found. Run ./scripts/init_project.sh first${NC}"
    exit 1
fi

source venv/bin/activate
export $(cat ../.env | grep -v '^#' | xargs)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

cd ..

# Wait for backend to start
echo "Waiting for backend to be ready..."
sleep 3

# Start frontend
echo -e "${GREEN}🎨 Starting frontend on port 3000...${NC}"
cd frontend

if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}Node modules not found. Run ./scripts/init_project.sh first${NC}"
    kill $BACKEND_PID
    exit 1
fi

npm run dev &
FRONTEND_PID=$!

cd ..

echo ""
echo -e "${GREEN}✅ Development environment is running!${NC}"
echo ""
echo "Services:"
echo "  🔧 Backend API:  http://localhost:8000"
echo "  🎨 Frontend:     http://localhost:3000"
echo "  📊 API Docs:     http://localhost:8000/docs"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"
echo ""

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID




