# Configuration Guide

This guide explains how to configure Workspace Guardian for your environment.

## Overview

Workspace Guardian requires configuration in three places:
1. **`.env`** - For local development
2. **`app.yaml`** - For Databricks Apps deployment
3. **`databricks.yml`** - For Databricks bundle configuration

## Required Configuration Values

### 1. SQL Warehouse ID

**Where to find it:**
1. Go to your Databricks workspace
2. Navigate to **SQL Warehouses**
3. Select your warehouse
4. Copy the **Warehouse ID** from Connection Details

**Where to set it:**
- `.env`: `DATABRICKS_WAREHOUSE_ID=<your-warehouse-id>`
- `app.yaml`: Update `DATABRICKS_WAREHOUSE_ID` value
- `databricks.yml`: Pass via `--var warehouse_id=<your-warehouse-id>`

### 2. Unity Catalog Name

**Where to find it:**
1. Go to your Databricks workspace
2. Navigate to **Data** or **Catalog**
3. Note your catalog name (e.g., "main", "production", "dev")

**Where to set it:**
- `.env`: `APP_CATALOG=<your-catalog-name>`
- `app.yaml`: Update `APP_CATALOG` value
- `databricks.yml`: Pass via `--var catalog=<your-catalog-name>`

### 3. Databricks Host & Token (Local Development Only)

**Where to find it:**
- **Host**: Your workspace URL (e.g., `https://your-workspace.cloud.databricks.com`)
- **Token**: Generate at **User Settings > Access Tokens**

**Where to set it:**
- `.env` only: 
  ```bash
  DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
  DATABRICKS_TOKEN=dapi...your-token-here
  ```

## Configuration Steps

### For Local Development

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` with your values:
   ```bash
   DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
   DATABRICKS_TOKEN=dapi1234567890abcdef
   DATABRICKS_WAREHOUSE_ID=abc123def456
   APP_CATALOG=main
   APP_SCHEMA=workspace_guardian
   ```

3. Run the application:
   ```bash
   ./scripts/run_dev.sh
   ```

### For Databricks Apps Deployment

1. Update `app.yaml` with your workspace values:
   ```yaml
   env:
     - name: DATABRICKS_WAREHOUSE_ID
       value: "YOUR_WAREHOUSE_ID"
     - name: APP_CATALOG
       value: "YOUR_CATALOG_NAME"
   ```

2. Deploy using the bundle with variables:
   ```bash
   databricks bundle deploy --target dev \
     --var catalog=main \
     --var warehouse_id=abc123def456
   ```

   Or use `databricks apps deploy`:
   ```bash
   ./deploy.sh
   ```

### Environment-Specific Configurations

You can create different configurations for different environments:

**Development:**
```bash
# .env.dev
APP_CATALOG=dev_catalog
APP_SCHEMA=workspace_guardian_dev
```

**Production:**
```bash
# .env.prod
APP_CATALOG=production
APP_SCHEMA=workspace_guardian
```

## Security Best Practices

1. ✅ **Never commit `.env` files** - They're in `.gitignore`
2. ✅ **Never commit tokens** - Use environment variables
3. ✅ **Use service principals** - Not personal access tokens for production
4. ✅ **Rotate tokens regularly** - Set expiration dates
5. ✅ **Use separate catalogs** - For dev, staging, and production

## Troubleshooting

### Error: "DATABRICKS_HOST and DATABRICKS_TOKEN must be set"
- **Solution**: Create a `.env` file from `.env.example` and fill in values

### Error: "Catalog not found"
- **Solution**: Verify your `APP_CATALOG` value matches your Unity Catalog name
- Check with: `databricks catalogs list`

### Error: "Warehouse not found"
- **Solution**: Verify your warehouse ID is correct
- Check with: `databricks sql-warehouses list`

### Error: "Permission denied"
- **Solution**: Ensure your token/service principal has:
  - USE CATALOG permission
  - CREATE SCHEMA permission
  - SQL Warehouse usage permission

## Configuration Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABRICKS_HOST` | Local dev only | - | Your workspace URL |
| `DATABRICKS_TOKEN` | Local dev only | - | Personal access token |
| `DATABRICKS_WAREHOUSE_ID` | Yes | - | SQL Warehouse ID |
| `APP_CATALOG` | Yes | `main` | Unity Catalog name |
| `APP_SCHEMA` | Yes | `workspace_guardian` | Schema name |
| `APP_VERSION` | No | `1.0.0` | Application version |
| `LOG_LEVEL` | No | `INFO` | Logging level |
| `PORT` | No | `8080` | Server port |

## Next Steps

After configuration:
1. Run local tests: `cd backend && pytest`
2. Test local server: `./scripts/run_dev.sh`
3. Deploy to Databricks: `./deploy.sh`
4. Monitor logs: `databricks apps logs workspace-guardian-dev`

