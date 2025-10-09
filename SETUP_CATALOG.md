# Unity Catalog Setup Guide

This guide walks you through setting up the required Unity Catalog resources for Workspace Guardian.

## Prerequisites

⚠️ **IMPORTANT**: You must have Unity Catalog admin privileges to create catalogs and schemas.

## Required Resources

The application requires:
1. **Catalog**: A Unity Catalog catalog (must be pre-created for security)
2. **Schema**: A schema within the catalog (auto-created if doesn't exist)
3. **SQL Warehouse**: A serverless or pro SQL warehouse to execute queries

### Security Model

- ❌ **Catalogs are NEVER auto-created** - must be created by Unity Catalog admin
- ✅ **Schemas ARE auto-created** - application will create them if needed
- ✅ **Tables ARE auto-created** - managed by migration system

## Step 1: Create Catalog

```sql
-- Create a catalog for Workspace Guardian
CREATE CATALOG IF NOT EXISTS workspace_guardian;

-- Grant usage to service principals/users who will run the app
GRANT USE CATALOG ON CATALOG workspace_guardian TO `<service_principal>`;
GRANT CREATE SCHEMA ON CATALOG workspace_guardian TO `<service_principal>`;
```

**Alternative**: Use an existing catalog like `main`:
```bash
# In .env file
DELTA_TABLE_NAME=main.workspace_guardian.approved_apps
```

## Step 2: Schema (Optional - Auto-Created)

⚠️ **The schema will be automatically created on first backend startup.**

However, if you prefer to create it manually:

```sql
-- Create schema for application tables (OPTIONAL)
CREATE SCHEMA IF NOT EXISTS workspace_guardian.guardian;

-- Grant usage and create table permissions
GRANT USE SCHEMA ON SCHEMA workspace_guardian.guardian TO `<service_principal>`;
GRANT CREATE TABLE ON SCHEMA workspace_guardian.guardian TO `<service_principal>`;
GRANT SELECT ON SCHEMA workspace_guardian.guardian TO `<service_principal>`;
GRANT MODIFY ON SCHEMA workspace_guardian.guardian TO `<service_principal>`;
```

**Note**: The service principal needs `CREATE SCHEMA` permission on the catalog for auto-creation to work.

## Step 3: Create SQL Warehouse

### Option A: Using Databricks UI

1. Go to **SQL Warehouses** in your Databricks workspace
2. Click **Create SQL Warehouse**
3. Configure:
   - **Name**: workspace-guardian-warehouse
   - **Cluster size**: 2X-Small (sufficient for most workloads)
   - **Type**: Serverless (recommended) or Pro
   - **Auto Stop**: 10 minutes
4. Click **Create**
5. Copy the **Warehouse ID** from the URL or details page

### Option B: Using Databricks CLI

```bash
databricks sql-warehouses create \
  --name workspace-guardian-warehouse \
  --cluster-size 2X-Small \
  --enable-serverless-compute \
  --auto-stop-mins 10
```

## Step 4: Configure Environment Variables

Update your `.env` file:

```bash
# Databricks Connection
DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
DATABRICKS_TOKEN=dapi...

# SQL Warehouse (get from UI or CLI)
DATABRICKS_WAREHOUSE_ID=abc123def456

# Unity Catalog Configuration
DELTA_TABLE_NAME=workspace_guardian.guardian.approved_apps

# Optional: Specify different catalog/schema
# DELTA_TABLE_NAME=main.my_schema.approved_apps
```

## Step 5: Verify Setup

Run the verification script:

```bash
# Load environment
export $(cat .env | xargs)

# Test connection and permissions
python scripts/check_migrations.py
```

Expected output:
```
🔍 Checking migrations for: workspace_guardian.guardian.approved_apps
📊 Migrations table: workspace_guardian.guardian.schema_migrations

⚠️  Migrations table does not exist yet
   (Will be created on first backend startup)

⚠️  Table does not exist yet: workspace_guardian.guardian.approved_apps
   (Will be created on first backend startup)
```

## Tables Created by Application

The application will automatically create these tables during startup:

### 1. `schema_migrations`
Tracks database schema version history.

| Column | Type | Description |
|--------|------|-------------|
| version | INT | Migration version number |
| description | STRING | What changed |
| applied_at | TIMESTAMP | When applied |
| success | BOOLEAN | Success status |

### 2. `approved_apps`
Stores approval records for applications and resources.

| Column | Type | Description |
|--------|------|-------------|
| app_name | STRING | Application name |
| app_id | STRING | Application ID |
| workspace_id | STRING | Databricks workspace ID |
| workspace_name | STRING | Workspace name |
| app_creator | STRING | Creator email |
| approved_by | STRING | Approver email |
| approval_date | TIMESTAMP | When approved |
| expiration_date | TIMESTAMP | When approval expires |
| justification | STRING | Approval reason |
| is_approved | BOOLEAN | Current approval status |
| revoked_date | TIMESTAMP | When revoked (if applicable) |
| revoked_by | STRING | Who revoked it |
| revoked_reason | STRING | Why revoked |
| updated_at | TIMESTAMP | Last update timestamp |

## Permissions Required

### Service Principal Permissions

The service principal running the application needs:

**Catalog Level:**
```sql
GRANT USE CATALOG ON CATALOG workspace_guardian TO `<service_principal>`;
```

**Schema Level:**
```sql
GRANT USE SCHEMA ON SCHEMA workspace_guardian.guardian TO `<service_principal>`;
GRANT CREATE TABLE ON SCHEMA workspace_guardian.guardian TO `<service_principal>`;
GRANT SELECT ON SCHEMA workspace_guardian.guardian TO `<service_principal>`;
GRANT MODIFY ON SCHEMA workspace_guardian.guardian TO `<service_principal>`;
```

**Warehouse Access:**
```sql
GRANT USE ON WAREHOUSE <warehouse_id> TO `<service_principal>`;
```

### Workspace-Level Permissions

The service principal also needs:
- **Workspace Admin** or **User** role
- Access to **Apps API**
- Access to **Model Serving API**
- Access to **Vector Search API**
- Access to **SQL API**

## Troubleshooting

### Error: Catalog does not exist

```
❌ Catalog does not exist: workspace_guardian
   Please create the catalog first: CREATE CATALOG workspace_guardian
```

**Solution:**
```sql
CREATE CATALOG IF NOT EXISTS workspace_guardian;
GRANT USE CATALOG ON CATALOG workspace_guardian TO `<service_principal>`;
```

### Error: Schema does not exist

```
❌ Schema does not exist: workspace_guardian.guardian
   Please create the schema first: CREATE SCHEMA workspace_guardian.guardian
```

**Solution:**
```sql
CREATE SCHEMA IF NOT EXISTS workspace_guardian.guardian;
GRANT USE SCHEMA ON SCHEMA workspace_guardian.guardian TO `<service_principal>`;
```

### Error: Insufficient permissions

```
Error: User does not have CREATE TABLE on SCHEMA workspace_guardian.guardian
```

**Solution:**
```sql
GRANT CREATE TABLE ON SCHEMA workspace_guardian.guardian TO `<service_principal>`;
GRANT MODIFY ON SCHEMA workspace_guardian.guardian TO `<service_principal>`;
```

### Error: Cannot access SQL Warehouse

```
Error: User does not have permission to use SQL Warehouse
```

**Solution:**
```sql
GRANT USE ON WAREHOUSE <warehouse_id> TO `<service_principal>`;
```

## Best Practices

### 1. Use Dedicated Catalog

Don't mix application tables with data tables:
- ✅ `workspace_guardian.guardian.approved_apps`
- ❌ `production_data.raw.approved_apps`

### 2. Use Service Principal

Use a service principal instead of user token:
```bash
DATABRICKS_TOKEN=<service_principal_token>
```

Benefits:
- No expiration on user leaving
- Clear audit trail
- Proper RBAC

### 3. Enable Auto-Stop on SQL Warehouse

Set auto-stop to 10-15 minutes:
- Saves costs
- Warehouse auto-starts when needed
- No impact on performance

### 4. Monitor Table Growth

```sql
-- Check table size
DESCRIBE DETAIL workspace_guardian.guardian.approved_apps;

-- View recent approvals
SELECT * 
FROM workspace_guardian.guardian.approved_apps 
WHERE approval_date > CURRENT_DATE - INTERVAL 7 DAYS;
```

### 5. Regular Backups

```sql
-- Create backup table
CREATE TABLE workspace_guardian.guardian.approved_apps_backup_20251009
AS SELECT * FROM workspace_guardian.guardian.approved_apps;
```

## Multi-Workspace Setup

If running across multiple Databricks workspaces:

### Option 1: Shared Unity Catalog (Recommended)

All workspaces write to the same catalog:
```bash
# Same for all workspaces
DELTA_TABLE_NAME=workspace_guardian.guardian.approved_apps
```

Benefits:
- Centralized approval tracking
- Single source of truth
- Easy reporting across workspaces

### Option 2: Separate Tables per Workspace

Each workspace has its own table:
```bash
# Workspace 1
DELTA_TABLE_NAME=workspace_guardian.guardian.approved_apps_ws1

# Workspace 2
DELTA_TABLE_NAME=workspace_guardian.guardian.approved_apps_ws2
```

Use when:
- Different compliance requirements
- Separate admin teams
- Data sovereignty requirements

## Next Steps

Once Unity Catalog is configured:

1. ✅ Catalog and schema created
2. ✅ SQL warehouse provisioned
3. ✅ Service principal permissions granted
4. ✅ Environment variables configured

Proceed to start the backend:
```bash
cd backend
source venv/bin/activate
export $(cat ../.env | xargs)
uvicorn app.main:app --reload
```

The application will automatically:
- Verify catalog and schema exist
- Create tables if needed
- Run pending migrations
- Start tracking approvals

🚀 You're ready to go!

