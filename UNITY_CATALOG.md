# Unity Catalog Integration

Workspace Guardian uses Unity Catalog to manage the approved apps Delta table. This provides enhanced governance, security, and management capabilities.

## Overview

Instead of using file paths (like `/dbfs/path/to/table`), the application uses Unity Catalog managed tables with a three-level namespace:

```
catalog.schema.table
```

Default table: `main.workspace_guardian.approved_apps`

## Benefits of Unity Catalog

### 1. **Centralized Governance**
- Fine-grained access control (GRANT/REVOKE)
- Column-level permissions
- Row-level security
- Audit logging of all data access

### 2. **Simplified Management**
- No need to manage file paths
- Automatic metadata management
- Schema evolution tracking
- Table lineage and data discovery

### 3. **ACID Guarantees**
- Atomic MERGE operations for upserts
- Transactional UPDATE operations
- No risk of partial writes
- Automatic conflict resolution

### 4. **Enterprise Features**
- Time travel (query historical data)
- Data versioning
- Automatic optimization
- Vacuum operations

## Configuration

### Environment Variable

Set the Unity Catalog table name in your `.env` file:

```bash
# Three-level namespace (catalog.schema.table)
DELTA_TABLE_NAME=main.workspace_guardian.approved_apps

# Or two-level (defaults to 'main' catalog)
DELTA_TABLE_NAME=workspace_guardian.approved_apps
```

### Table Structure

The table is automatically created with the following structure:

```sql
Catalog:  main
Schema:   workspace_guardian  
Table:    approved_apps
```

## Automatic Table Creation

The application automatically:

1. **Creates the catalog** (if it doesn't exist and you have permissions)
2. **Creates the schema** (if it doesn't exist)
3. **Creates the table** (if it doesn't exist)

If you don't have permission to create catalogs or schemas, ensure they exist before starting the application.

## Manual Setup (Optional)

If you prefer to create the table manually or need specific configurations:

### Create Catalog and Schema

```sql
-- Create catalog (may require account admin)
CREATE CATALOG IF NOT EXISTS main;

-- Use the catalog
USE CATALOG main;

-- Create schema
CREATE SCHEMA IF NOT EXISTS workspace_guardian
COMMENT 'Workspace Guardian application data';
```

### Create Table

```sql
CREATE TABLE IF NOT EXISTS main.workspace_guardian.approved_apps (
    app_name STRING COMMENT 'Name of the application',
    app_id STRING COMMENT 'Unique application identifier',
    workspace_id STRING COMMENT 'Databricks workspace ID',
    workspace_name STRING COMMENT 'Workspace display name',
    app_creator STRING COMMENT 'User who created the app',
    approved_by STRING COMMENT 'User who approved the app',
    approval_date TIMESTAMP COMMENT 'Timestamp of approval',
    expiration_date TIMESTAMP COMMENT 'Optional expiration date',
    justification STRING COMMENT 'Reason for approval',
    is_approved BOOLEAN COMMENT 'Current approval status',
    revoked_date TIMESTAMP COMMENT 'Timestamp when revoked',
    revoked_by STRING COMMENT 'User who revoked approval',
    updated_at TIMESTAMP COMMENT 'Last update timestamp'
)
USING DELTA
COMMENT 'Approved Databricks resources with audit trail'
TBLPROPERTIES (
    'delta.enableChangeDataFeed' = 'true',
    'delta.autoOptimize.optimizeWrite' = 'true',
    'delta.autoOptimize.autoCompact' = 'true'
);
```

## Permissions

### Required Permissions

The service account or user running the application needs:

1. **Catalog Level**:
   - `USE CATALOG` on the target catalog
   - `CREATE SCHEMA` (if creating new schema)

2. **Schema Level**:
   - `USE SCHEMA` on the target schema
   - `CREATE TABLE` (if creating new table)

3. **Table Level**:
   - `SELECT` - Read approved apps
   - `INSERT` - Add new approvals
   - `UPDATE` - Revoke approvals, update records
   - `MODIFY` - For MERGE operations

### Granting Permissions

```sql
-- Grant permissions to a service principal
GRANT USE CATALOG ON CATALOG main TO `service-principal-name`;
GRANT USE SCHEMA ON SCHEMA main.workspace_guardian TO `service-principal-name`;
GRANT CREATE TABLE ON SCHEMA main.workspace_guardian TO `service-principal-name`;

-- Grant table permissions (after table is created)
GRANT SELECT, INSERT, UPDATE, MODIFY 
ON TABLE main.workspace_guardian.approved_apps 
TO `service-principal-name`;
```

### For Groups

```sql
-- Grant to a group instead
GRANT USE CATALOG ON CATALOG main TO `workspace-guardian-admins`;
GRANT ALL PRIVILEGES ON SCHEMA main.workspace_guardian TO `workspace-guardian-admins`;
GRANT ALL PRIVILEGES ON TABLE main.workspace_guardian.approved_apps TO `workspace-guardian-admins`;
```

## Advanced Operations

### Query Historical Data (Time Travel)

```sql
-- View approvals as of specific timestamp
SELECT * FROM main.workspace_guardian.approved_apps 
TIMESTAMP AS OF '2024-01-01 00:00:00';

-- View approvals as of specific version
SELECT * FROM main.workspace_guardian.approved_apps 
VERSION AS OF 10;
```

### Table Maintenance

```sql
-- Optimize table (consolidate small files)
OPTIMIZE main.workspace_guardian.approved_apps;

-- Optimize with Z-ordering for better query performance
OPTIMIZE main.workspace_guardian.approved_apps
ZORDER BY (workspace_id, app_id);

-- Vacuum old files (default retention: 7 days)
VACUUM main.workspace_guardian.approved_apps;

-- Vacuum with custom retention
VACUUM main.workspace_guardian.approved_apps RETAIN 168 HOURS;
```

### View Table History

```sql
-- See all versions
DESCRIBE HISTORY main.workspace_guardian.approved_apps;

-- See recent changes
DESCRIBE HISTORY main.workspace_guardian.approved_apps LIMIT 10;
```

### Enable Change Data Feed

```sql
-- Enable CDC for downstream processing
ALTER TABLE main.workspace_guardian.approved_apps
SET TBLPROPERTIES (delta.enableChangeDataFeed = true);

-- Query changes
SELECT * FROM table_changes('main.workspace_guardian.approved_apps', 0);
```

## Using Different Catalogs

To use a different catalog or schema:

1. **Update environment variable**:
```bash
DELTA_TABLE_NAME=my_catalog.my_schema.approved_apps
```

2. **Ensure catalog and schema exist**:
```sql
CREATE CATALOG IF NOT EXISTS my_catalog;
CREATE SCHEMA IF NOT EXISTS my_catalog.my_schema;
```

3. **Grant appropriate permissions** to the service account

## Monitoring and Auditing

### View Access Logs

Unity Catalog automatically logs all access. View in:
- Databricks UI: Data Explorer → Table → Audit Log
- System tables: `system.access.audit`

### Query Audit Information

```sql
-- See who accessed the table
SELECT 
    user_identity.email,
    action_name,
    request_params.full_name_arg,
    event_time
FROM system.access.audit
WHERE request_params.full_name_arg = 'main.workspace_guardian.approved_apps'
ORDER BY event_time DESC
LIMIT 100;
```

## Troubleshooting

### "Table not found"
- Verify catalog and schema exist
- Check permissions
- Confirm table name format is correct

### "Permission denied"
- Ensure you have required permissions (USE CATALOG, USE SCHEMA, etc.)
- Check if you're using the correct principal
- Verify group memberships

### "Catalog does not exist"
- Create catalog manually or use 'main' catalog
- Check if you have CREATE CATALOG permission
- Use an existing catalog

### "Schema does not exist"
- Create schema manually
- Verify catalog name is correct
- Check CREATE SCHEMA permission

## Best Practices

1. **Use Service Principals** for production deployments
2. **Enable Change Data Feed** for audit trail
3. **Set up regular OPTIMIZE** jobs for performance
4. **Configure appropriate VACUUM** retention
5. **Use Z-ORDERING** on frequently queried columns
6. **Implement least-privilege** access control
7. **Monitor table size** and partition if needed
8. **Enable auto-optimization** for better performance
9. **Document access policies** in table comments
10. **Regular backups** using Delta's time travel

## Migration from File Paths

If you were previously using file paths:

### Old Configuration
```bash
DELTA_TABLE_PATH=/dbfs/workspace_guardian/approved_apps
```

### New Configuration
```bash
DELTA_TABLE_NAME=main.workspace_guardian.approved_apps
```

### Migration Steps

1. **Create Unity Catalog table**:
```sql
CREATE TABLE main.workspace_guardian.approved_apps
USING DELTA
LOCATION 'dbfs:/workspace_guardian/approved_apps';
```

2. **Update environment variable**

3. **Test the connection**:
```bash
python scripts/test_connection.py
```

4. **Verify data is accessible**

## Additional Resources

- [Unity Catalog Documentation](https://docs.databricks.com/data-governance/unity-catalog/index.html)
- [Delta Lake Guide](https://docs.databricks.com/delta/index.html)
- [Access Control](https://docs.databricks.com/security/access-control/unity-catalog/index.html)
- [Best Practices](https://docs.databricks.com/data-governance/unity-catalog/best-practices.html)

---

**Note**: Unity Catalog is the recommended approach for all production deployments of Workspace Guardian.


