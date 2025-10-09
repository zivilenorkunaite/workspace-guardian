#!/bin/bash

set -e

echo "🚀 Deploying Workspace Guardian as Databricks App"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Step 1: Build Frontend
echo -e "\n${BLUE}Step 1: Building Frontend${NC}"
cd frontend
npm install
npm run build
cd ..
echo -e "${GREEN}✅ Frontend built${NC}"

# Step 2: Prepare app directory
echo -e "\n${BLUE}Step 2: Preparing app directory${NC}"
rm -rf app/backend app/frontend
mkdir -p app/backend app/frontend/dist

# Copy backend code
cp -r backend/app app/backend/
cp backend/requirements.txt app/requirements.txt

# Copy frontend build
cp -r frontend/dist/* app/frontend/dist/

echo -e "${GREEN}✅ App directory prepared${NC}"

# Step 3: Validate bundle
echo -e "\n${BLUE}Step 3: Validating Databricks bundle${NC}"
databricks bundle validate --target dev
echo -e "${GREEN}✅ Bundle validated${NC}"

# Step 4: Deploy
echo -e "\n${BLUE}Step 4: Deploying to Databricks${NC}"
databricks bundle deploy --target dev
echo -e "${GREEN}✅ Bundle deployed${NC}"

# Step 5: Get app URL
echo -e "\n${BLUE}Step 5: Getting app URL${NC}"
APP_URL=$(databricks apps list | grep workspace-guardian-dev | awk '{print $NF}')

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}✅ Deployment Complete!${NC}"
echo ""
echo "App URL: ${APP_URL}"
echo ""
echo "To view logs:"
echo "  databricks apps logs workspace-guardian-dev"
echo ""
echo "To stop the app:"
echo "  databricks apps stop workspace-guardian-dev"
echo ""
echo "To delete the app:"
echo "  databricks apps delete workspace-guardian-dev"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"


