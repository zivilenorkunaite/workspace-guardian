#!/bin/bash
# Startup script for Databricks App - runs both frontend and backend

set -e

echo "🚀 Starting Workspace Guardian"
echo "================================"

# Install frontend dependencies if needed
echo "📦 Checking frontend dependencies..."
cd /app/python/source_code/frontend
if [ ! -d "node_modules" ]; then
    echo "📦 Installing npm dependencies..."
    npm install --production
    echo "✅ Dependencies installed"
else
    echo "✅ Dependencies already installed"
fi

# Start backend on port 8000 (internal)
echo "📡 Starting Backend (FastAPI) on port 8000..."
cd /app/python/source_code
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
echo "✅ Backend started (PID: $BACKEND_PID)"

# Wait for backend to be ready
echo "⏳ Waiting for backend to be ready..."
sleep 5

# Start frontend on port 8080 (exposed)
echo "🎨 Starting Frontend (Vite) on port 8080..."
cd /app/python/source_code/frontend
npm run dev -- --host 0.0.0.0 --port 8080 &
FRONTEND_PID=$!
echo "✅ Frontend started (PID: $FRONTEND_PID)"

echo ""
echo "================================"
echo "✅ Workspace Guardian is running!"
echo "📡 Backend:  http://localhost:8000 (internal)"
echo "🎨 Frontend: http://localhost:8080 (public)"
echo "================================"

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID

