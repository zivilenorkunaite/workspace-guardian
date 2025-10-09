#!/bin/bash
set -e

echo "🚀 Initializing Workspace Guardian Project..."
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -f "README.md" ]; then
    echo -e "${RED}Error: Please run this script from the project root directory${NC}"
    exit 1
fi

# Check prerequisites
echo "📋 Checking prerequisites..."

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed${NC}"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)

echo -e "${GREEN}✅ Python $PYTHON_VERSION found${NC}"

# Warn if Python 3.13+ (packages may not have wheels yet)
if [ "$PYTHON_MAJOR" -ge 3 ] && [ "$PYTHON_MINOR" -ge 13 ]; then
    echo -e "${YELLOW}⚠️  Warning: Python 3.13+ detected. Some packages may not have pre-built wheels.${NC}"
    echo -e "${YELLOW}   For faster installation, consider using Python 3.11 or 3.12.${NC}"
    echo -e "${YELLOW}   Continue anyway? This may take 10-15 minutes to compile packages. (y/N)${NC}"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        echo "Installation cancelled. Please use Python 3.11 or 3.12 for optimal experience."
        exit 1
    fi
fi

# Check Node.js
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js is not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Node.js found${NC}"

# Check npm
if ! command -v npm &> /dev/null; then
    echo -e "${RED}❌ npm is not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✅ npm found${NC}"

echo ""
echo "🔧 Setting up backend..."

# Setup backend
cd backend

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing Python dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

echo -e "${GREEN}✅ Backend setup complete${NC}"

cd ..

echo ""
echo "🎨 Setting up frontend..."

# Setup frontend
cd frontend

# Install dependencies
echo "Installing Node.js dependencies..."
npm install --silent

echo -e "${GREEN}✅ Frontend setup complete${NC}"

cd ..

echo ""
echo "📝 Setting up environment configuration..."

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cat > .env << 'EOF'
# Databricks Configuration
DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
DATABRICKS_TOKEN=your-databricks-token

# Delta Table Configuration
DELTA_TABLE_PATH=/dbfs/workspace_guardian/approved_apps

# Optional: For multi-workspace support
# DATABRICKS_ACCOUNT_ID=your-account-id
# DATABRICKS_ACCOUNT_TOKEN=your-account-token
EOF
    echo -e "${YELLOW}⚠️  Please edit .env file with your Databricks credentials${NC}"
else
    echo -e "${GREEN}✅ .env file already exists${NC}"
fi

# Create frontend .env if it doesn't exist
if [ ! -f "frontend/.env" ]; then
    echo "Creating frontend/.env file..."
    cat > frontend/.env << 'EOF'
# API Base URL
VITE_API_URL=/api
EOF
    echo -e "${GREEN}✅ Frontend .env created${NC}"
else
    echo -e "${GREEN}✅ Frontend .env file already exists${NC}"
fi

echo ""
echo "✨ Project initialization complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your Databricks credentials"
echo "2. Start the backend:"
echo "   cd backend"
echo "   source venv/bin/activate"
echo "   export \$(cat ../.env | xargs)"
echo "   uvicorn app.main:app --reload"
echo ""
echo "3. In a new terminal, start the frontend:"
echo "   cd frontend"
echo "   npm run dev"
echo ""
echo "4. Open http://localhost:3000 in your browser"
echo ""
echo -e "${GREEN}Happy coding! 🎉${NC}"


