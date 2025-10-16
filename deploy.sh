#!/bin/bash
# Simple deployment script - Databricks handles the build automatically

set -e

echo "🚀 Deploying Workspace Guardian to Databricks Apps"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Get current user and bundle path
CURRENT_USER=$(databricks current-user me --output json | python3 -c "import sys, json; print(json.load(sys.stdin)['userName'])")
BUNDLE_PATH="/Workspace/Users/${CURRENT_USER}/.bundle/workspace-guardian/dev/files"

echo -e "${BLUE}📦 Deployment Configuration:${NC}"
echo "   User: ${CURRENT_USER}"
echo "   Bundle path: ${BUNDLE_PATH}"
echo ""

# Step 1: Validate bundle
echo -e "${BLUE}Step 1: Validating Databricks bundle${NC}"
if databricks bundle validate --target dev; then
    echo -e "${GREEN}✅ Bundle validated${NC}"
else
    echo -e "${RED}❌ Bundle validation failed${NC}"
    exit 1
fi

# Step 2: Deploy bundle (uploads source code)
echo -e "\n${BLUE}Step 2: Deploying bundle to workspace${NC}"
echo -e "${YELLOW}⏳ This uploads source code to workspace...${NC}"
if databricks bundle deploy --target dev; then
    echo -e "${GREEN}✅ Source code uploaded${NC}"
else
    echo -e "${RED}❌ Bundle deployment failed${NC}"
    exit 1
fi

# Step 3: Deploy app (Databricks builds automatically)
echo -e "\n${BLUE}Step 3: Deploying app${NC}"
echo -e "${YELLOW}⏳ Databricks will:${NC}"
echo -e "${YELLOW}   1. Run npm install${NC}"
echo -e "${YELLOW}   2. Run pip install -r requirements.txt${NC}"
echo -e "${YELLOW}   3. Run npm run start${NC}"
echo ""

if databricks apps deploy workspace-guardian-dev \
  --source-code-path ${BUNDLE_PATH} \
  --mode SNAPSHOT \
  --timeout 10m; then
    echo -e "${GREEN}✅ App deployed successfully${NC}"
else
    echo -e "${RED}❌ App deployment failed${NC}"
    exit 1
fi

# Step 4: Get app status
echo -e "\n${BLUE}Step 4: Checking app status${NC}"
APP_INFO=$(databricks apps get workspace-guardian-dev --output json)
APP_STATUS=$(echo "$APP_INFO" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['app_status']['state'])")
APP_URL=$(echo "$APP_INFO" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('url', 'N/A'))")

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ "$APP_STATUS" = "RUNNING" ]; then
    echo -e "${GREEN}🎉 Deployment Complete!${NC}"
else
    echo -e "${YELLOW}⚠️  Deployment complete, but app is not running yet${NC}"
fi
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "${BLUE}📱 App URL:${NC}"
echo "   ${APP_URL}"
echo ""
echo -e "${BLUE}📊 App Status:${NC} ${APP_STATUS}"
echo ""
echo -e "${BLUE}📋 Useful Commands:${NC}"
echo "   View logs:    databricks apps logs workspace-guardian-dev"
echo "   Check status: databricks apps get workspace-guardian-dev"
echo "   Stop app:     databricks apps stop workspace-guardian-dev"
echo "   Start app:    databricks apps start workspace-guardian-dev"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

