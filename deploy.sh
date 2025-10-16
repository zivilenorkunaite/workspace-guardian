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

# Step 4: Upload to Databricks Workspace
echo -e "\n${BLUE}Step 4: Uploading to Databricks Workspace${NC}"
databricks bundle deploy --target dev
echo -e "${GREEN}✅ Files uploaded to workspace${NC}"

# Step 5: Deploy app to Databricks Apps
echo -e "\n${BLUE}Step 5: Deploying app code${NC}"
databricks apps deploy workspace-guardian-dev \
  --source-code-path /Workspace/Users/$(databricks current-user me --output json | python3 -c "import sys, json; print(json.load(sys.stdin)['userName'])")/.bundle/workspace-guardian/dev/files/app \
  --mode SNAPSHOT
echo -e "${GREEN}✅ App deployed${NC}"

# Step 6: Verify app status
echo -e "\n${BLUE}Step 6: Verifying app status${NC}"
APP_STATUS=$(databricks apps get workspace-guardian-dev --output json | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['app_status']['state'])")
APP_URL=$(databricks apps get workspace-guardian-dev --output json | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['url'])")

if [ "$APP_STATUS" = "RUNNING" ]; then
    echo -e "${GREEN}✅ App is RUNNING${NC}"
else
    echo -e "${RED}⚠️  App status: $APP_STATUS${NC}"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}🎉 Deployment Complete!${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "${BLUE}📱 App URL:${NC}"
echo "   $APP_URL"
echo ""
echo -e "${BLUE}📊 App Status:${NC} $APP_STATUS"
echo ""
echo -e "${BLUE}📋 Useful Commands:${NC}"
echo "   View logs:   databricks apps logs workspace-guardian-dev"
echo "   Check status: databricks apps get workspace-guardian-dev"
echo "   Stop app:    databricks apps stop workspace-guardian-dev"
echo "   Start app:   databricks apps start workspace-guardian-dev"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"


