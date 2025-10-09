# Setup Guide - Workspace Guardian

This guide will help you set up and deploy the Workspace Guardian application for monitoring Databricks resources.

## Prerequisites

1. **Databricks Workspace** with Unity Catalog enabled
2. **Python 3.11 or 3.12** installed (recommended)
   - Python 3.9+ will work, but 3.11/3.12 have better package support
3. **Node.js 16+** and npm installed
4. **Databricks Personal Access Token** with permissions:
   - Read access to Apps, Serving Endpoints, Vector Search, and Connections
   - Write access to Unity Catalog (for approval table)
   - SQL Warehouse access (for Delta table operations)

## Quick Setup (Recommended)

We provide automated setup scripts for convenience:

```bash
# Initialize everything (installs dependencies)
./scripts/init_project.sh

# Configure environment variables
cp env.template .env
# Edit .env with your Databricks credentials

# Start both backend and frontend
./scripts/run_dev.sh
```

That's it! Skip to [Step 7: Test Locally](#step-7-test-locally) if using quick setup.

## Manual Setup

If you prefer manual setup or the scripts don't work for your environment, follow these steps:

## Step 1: Navigate to Project

```bash
cd /path/to/workspace-guardian
```

## Step 2: Configure Environment Variables

Copy the template and edit with your credentials:

```bash
cp env.template .env
nano .env  # or use your preferred editor
```

Required environment variables:

```bash
# Databricks Configuration
DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
DATABRICKS_TOKEN=dapi_your_token_here

# Unity Catalog Configuration
DELTA_TABLE_NAME=catalog.schema.approved_apps
# Example: main.workspace_guardian.approved_apps

# SQL Warehouse (for Delta table operations)
DATABRICKS_WAREHOUSE_ID=your_warehouse_id
```

### Getting Your Databricks Token

1. Log in to your Databricks workspace
2. Click your username (top right)
3. Go to "User Settings"
4. Select "Access Tokens" tab
5. Click "Generate New Token"
6. Give it a name and optional expiration
7. Copy the token (you won't see it again!)

### Getting Your Warehouse ID

1. In Databricks, go to "SQL Warehouses"
2. Click on your warehouse
3. Copy the ID from the URL or warehouse details

## Step 3: Set Up Backend

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Step 4: Initialize Unity Catalog Table

The Unity Catalog table will be automatically created when you first start the backend. The table schema includes:

- Resource details (name, ID, workspace, creator)
- Approval information (approved_by, approval_date, expiration_date, justification)
- Revocation tracking (revoked_date, revoked_by, revoked_reason)
- Audit fields (is_approved, updated_at)

**Note:** Ensure your Unity Catalog has the specified catalog and schema, or the app will create them with appropriate permissions.

## Step 5: Set Up Frontend

```bash
cd ../frontend

# Install dependencies
npm install
```

## Step 6: Local Development

### Option A: Using Helper Scripts (Recommended)

```bash
# Terminal 1 - Backend
./start-backend.sh

# Terminal 2 - Frontend
./start-frontend.sh
```

### Option B: Manual Start

**Terminal 1 - Backend:**

```bash
cd backend
source venv/bin/activate  # or venv\Scripts\activate on Windows
export $(cat ../.env | xargs)  # Load environment variables (Mac/Linux)
# On Windows: use set command or load .env manually
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**

```bash
cd frontend
npm run dev
```

### Access Points

- **Frontend UI:** `http://localhost:3000`
- **Backend API:** `http://localhost:8000`
- **API Documentation:** `http://localhost:8000/docs` (Swagger UI)

## Step 7: Test Locally

1. Open `http://localhost:3000` in your browser
2. You should see the Workspace Guardian interface with:
   - Overall Resources statistics (top row)
   - Individual resource type sections (Apps, Model Serving, Vector Search, Lakehouse Postgres)
3. Select a workspace from the dropdown (if multi-workspace is configured)
4. View all resources and their current states
5. Test approval workflow:
   - Click "Approve App" on an unapproved resource
   - Fill in justification and optional expiration date
   - Verify approval appears with green checkmark
6. Test revoke workflow:
   - Click "Revoke Approval" on an approved resource
   - Provide revocation reason
   - Verify resource shows as unapproved

## Step 8: Deploy to Databricks Apps

### Option 1: Using Databricks CLI

```bash
# From the root directory
databricks apps create workspace-guardian \
  --description "Databricks Resources Monitor & Approval Management"

databricks apps deploy workspace-guardian
```

### Option 2: Using Databricks UI

1. Navigate to your Databricks workspace
2. Go to "Apps" in the sidebar
3. Click "Create App"
4. Upload your project files
5. Configure environment variables
6. Deploy

## Configuration for Databricks Apps

Make sure your `databricks.yml` is properly configured:

```yaml
bundle:
  name: workspace-guardian

resources:
  apps:
    workspace_guardian:
      name: workspace-guardian
      description: Monitor and manage Databricks resource approvals across workspaces
```

## Troubleshooting

### Backend Issues

**Error: "DATABRICKS_HOST and DATABRICKS_TOKEN must be set"**
- Ensure your `.env` file exists in the project root
- Check environment variables are loaded correctly
- Verify no typos in variable names

**Error: "DATABRICKS_WAREHOUSE_ID must be set"**
- Add the warehouse ID to your `.env` file
- Get the ID from SQL Warehouses section in Databricks

**Error: "Failed to initialize Unity Catalog table"**
- Check your token has Unity Catalog write permissions
- Verify the catalog and schema exist (or you have permission to create them)
- Ensure the warehouse is running and accessible

**Error: "1 validation error for DatabricksApp state"**
- This is usually fixed by restarting the backend
- Check that all resource types are properly configured

### Frontend Issues

**Error: "Failed to load workspaces"**
- Ensure the backend is running
- Check CORS settings in the backend
- Verify API_BASE_URL in frontend configuration

**Error: "Module not found"**
- Run `npm install` again
- Clear node_modules and reinstall: `rm -rf node_modules && npm install`

### Unity Catalog Issues

**Table not created**
- Ensure your token has Unity Catalog permissions
- Check the catalog and schema exist or can be created
- Verify SQL Warehouse is running and accessible
- Check warehouse ID is correct in `.env`

**Permission errors**
- Grant necessary permissions on the catalog/schema
- See `UNITY_CATALOG.md` for detailed permission setup

## Monitoring and Logs

### Backend Logs

```bash
# View backend logs
tail -f backend/logs/app.log
```

### Frontend Build

```bash
# Build for production
cd frontend
npm run build

# Preview production build
npm run preview
```

## Security Considerations

1. **Never commit `.env` file** to version control
2. **Rotate tokens regularly** for security
3. **Use service principals** for production deployments
4. **Enable authentication** for production use
5. **Review approval justifications** regularly

## Production Deployment Checklist

- [ ] Environment variables configured in production environment
- [ ] Unity Catalog table with proper governance policies
- [ ] Service principal configured (not personal access token)
- [ ] SQL Warehouse with appropriate size for workload
- [ ] CORS settings configured for production domain
- [ ] Error logging and monitoring enabled
- [ ] Unity Catalog backup/retention policies configured
- [ ] User authentication implemented (OAuth/SAML)
- [ ] Rate limiting configured on API endpoints
- [ ] Resource monitoring across all types enabled

## Maintenance

### Updating Dependencies

```bash
# Backend
cd backend
pip list --outdated
pip install --upgrade package-name

# Frontend
cd frontend
npm outdated
npm update package-name
```

### Unity Catalog Table Maintenance

```sql
-- Optimize table periodically
OPTIMIZE catalog.schema.approved_apps;

-- Vacuum old versions (removes old data files, cannot be undone)
-- Run this periodically to save storage
VACUUM catalog.schema.approved_apps RETAIN 168 HOURS;

-- View table history
DESCRIBE HISTORY catalog.schema.approved_apps;
```

## Resources Monitored

The application currently tracks:
- **Databricks Apps** - Custom applications deployed via Databricks Apps
- **Model Serving Endpoints** - ML model serving infrastructure
- **Vector Search Endpoints** - Vector database endpoints for embeddings
- **Lakehouse Postgres** - PostgreSQL connections via Lakebase

## Additional Documentation

- **README.md** - Project overview and features
- **QUICKSTART.md** - 5-minute quick start guide
- **UNITY_CATALOG.md** - Unity Catalog setup and permissions
- **DEPLOYMENT.md** - Production deployment guide
- **CHANGELOG.md** - Version history and changes

## Support

For issues and questions:
- Review the documentation files listed above
- Check Databricks Unity Catalog documentation
- Review FastAPI and React documentation
- Consult Databricks Apps documentation

## Next Steps

After successful setup:
1. Test all resource types are detected correctly
2. Verify approval workflow for each resource type
3. Set up Unity Catalog governance policies
4. Configure monitoring and alerts
5. Implement user authentication for production
6. Document any workspace-specific configuration
7. Schedule regular table maintenance (OPTIMIZE/VACUUM)


