# Databricks App Deployment Guide

This application can be deployed as a Databricks App using Databricks Asset Bundles (DAB).

## Prerequisites

1. **Databricks CLI** installed and configured:
   ```bash
   pip install databricks-cli
   databricks configure
   ```

2. **Databricks Workspace** with:
   - Unity Catalog enabled
   - SQL Warehouse created
   - App will run with its own identity (no tokens needed)

3. **Unity Catalog** setup:
   ```sql
   -- Create catalog (one-time, by admin)
   CREATE CATALOG IF NOT EXISTS main;
   
   -- Grant permissions to service principal
   GRANT USE CATALOG ON CATALOG main TO `<service-principal-id>`;
   GRANT CREATE SCHEMA ON CATALOG main TO `<service-principal-id>`;
   ```

## Deployment Options

### Option 1: Quick Deploy (Recommended)

```bash
./deploy.sh
```

This script will:
1. Build the frontend
2. Prepare the app directory
3. Validate the bundle
4. Deploy to Databricks
5. Show the app URL

### Option 2: Manual Deployment

#### Step 1: Build Frontend
```bash
cd frontend
npm install
npm run build
cd ..
```

#### Step 2: Prepare App Directory
```bash
# Clean and create
rm -rf app/backend app/frontend
mkdir -p app/backend app/frontend/dist

# Copy backend
cp -r backend/app app/backend/
cp backend/requirements.txt app/requirements.txt

# Copy frontend build
cp -r frontend/dist/* app/frontend/dist/
```

#### Step 3: Configure Variables
Edit `databricks.yml` and set:
- `catalog`: Your Unity Catalog name (default: main)
- `schema`: Schema name (default: workspace_guardian)
- `warehouse_id`: Your SQL Warehouse ID

Or pass as command-line args:
```bash
databricks bundle deploy \
  --target dev \
  --var catalog=your_catalog \
  --var schema=your_schema \
  --var warehouse_id=your_warehouse_id
```

#### Step 4: Deploy
```bash
# Validate first
databricks bundle validate --target dev

# Deploy
databricks bundle deploy --target dev
```

## Environment Targets

### Development (`dev`)
- Default target
- Uses `development` mode
- App name: `workspace-guardian-dev`

### Production (`prod`)
- Production mode
- App name: `workspace-guardian-prod`
- Deploy with: `databricks bundle deploy --target prod`

## Managing the App

### View Logs
```bash
databricks apps logs workspace-guardian-dev --follow
```

### Start/Stop
```bash
databricks apps start workspace-guardian-dev
databricks apps stop workspace-guardian-dev
```

### Update
```bash
# After code changes, redeploy
databricks bundle deploy --target dev
```

### Delete
```bash
databricks apps delete workspace-guardian-dev
databricks bundle destroy --target dev
```

## Application Structure

```
workspace-guardian/
├── databricks.yml          # Main bundle configuration
├── deploy.sh               # Deployment script
├── app/                    # Deployed app directory
│   ├── databricks-app.json # App metadata
│   ├── app.yaml           # App configuration
│   ├── requirements.txt   # Python dependencies
│   ├── backend/           # Backend code (copied)
│   │   └── app/
│   └── frontend/          # Frontend build (copied)
│       └── dist/
├── backend/               # Backend source
└── frontend/              # Frontend source
```

## Configuration

### Environment Variables

The app uses these environment variables (automatically set by DAB):

- `DATABRICKS_WAREHOUSE_ID`: SQL Warehouse ID
- `APP_CATALOG`: Unity Catalog name
- `APP_SCHEMA`: Schema name
- `APP_VERSION`: Application version

**Note**: `DATABRICKS_HOST` and `DATABRICKS_TOKEN` are NOT needed when running as a Databricks App. The app automatically authenticates using its own identity.

### Permissions Required

The app needs these permissions:
- **SQL**: Execute queries on SQL Warehouse
- **Workspace**: Read workspace resources (apps, endpoints)
- **Unity Catalog**: Read/write to catalog and schema

## Troubleshooting

### Bundle Validation Fails
```bash
# Check bundle configuration
databricks bundle validate --target dev --verbose
```

### App Fails to Start
```bash
# Check logs
databricks apps logs workspace-guardian-dev

# Verify app permissions
databricks apps get workspace-guardian-dev
```

### Migration Errors
- Ensure catalog exists (must be pre-created by admin)
- Verify service principal has permissions
- Check SQL Warehouse is running

### Frontend Not Loading
- Ensure `npm run build` completed successfully
- Check `frontend/dist` directory exists and has files
- Verify static files are copied to `app/frontend/dist`

## Authentication

Databricks Apps use **automatic authentication** via the app's identity:

- **No tokens needed** - The app runs with its own service principal
- **No secrets to manage** - Authentication is handled by Databricks
- **Identity-based permissions** - Grant permissions directly to the app

### Grant Permissions to App

After deploying, grant the app permissions:

```sql
-- Grant catalog access to the app's service principal
GRANT USE CATALOG ON CATALOG main TO `<app-service-principal>`;
GRANT CREATE SCHEMA ON CATALOG main TO `<app-service-principal>`;

-- Grant SQL Warehouse access
-- (Done via Databricks UI or API)
```

## Production Deployment

For production:

1. Deploy to `prod` target:
   ```bash
   databricks bundle deploy --target prod \
     --var catalog=prod_catalog \
     --var warehouse_id=prod_warehouse_id
   ```
2. Grant permissions to the app's service principal
3. Set up monitoring and alerts
4. Configure backup and disaster recovery
5. No tokens or secrets needed - app uses its own identity

## URLs and Endpoints

After deployment:
- **App URL**: `https://<workspace>.cloud.databricks.com/apps/<app-name>`
- **API Endpoint**: `https://<workspace>.cloud.databricks.com/apps/<app-name>/api`
- **Health Check**: `https://<workspace>.cloud.databricks.com/apps/<app-name>/api/health`

## Support

For issues:
1. Check logs: `databricks apps logs workspace-guardian-dev`
2. Validate bundle: `databricks bundle validate --verbose`
3. Review deployment guide
4. Check Databricks documentation: https://docs.databricks.com/dev-tools/bundles/apps.html
