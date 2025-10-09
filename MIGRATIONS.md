# Database Migrations Guide

This document explains how the database migration system works and how to add new migrations.

## Overview

The Workspace Guardian application uses a **versioned migration system** to manage Delta table schema changes. This ensures:
- ✅ Consistent schema across environments
- ✅ Clear audit trail of changes
- ✅ Safe, idempotent migrations
- ✅ Easy rollback capability

## Architecture

### File Structure

```
backend/app/
├── migrations.py       # Migration definitions (add new ones here)
└── delta_manager.py    # Migration execution logic (don't modify)
```

### Migration Flow

```
Backend Startup
    ↓
Parse Table Name (catalog.schema.table)
    ↓
Verify Catalog Exists (fail if not)
    ↓
Create Schema if Needed (automatic)
    ↓
Load Migrations from migrations.py
    ↓
Validate Migration Schema
    ↓
Create schema_migrations Table (if needed)
    ↓
Get List of Applied Migrations
    ↓
For Each Migration:
    ├─ Already Applied? → ⏭️ [SKIP]
    └─ Not Applied? → 🔧 [APPLY]
        ├─ Success → ✅ [SUCCESS] Record
        └─ Failure → ❌ [FAILED] Log error
    ↓
Show Migration Summary
```

## Migration Tracking

### Migrations Table

All applied migrations are tracked in: `{catalog}.{schema}.schema_migrations`

**Schema:**
```sql
CREATE TABLE schema_migrations (
    version INT,              -- Migration version number
    description STRING,       -- Human-readable description
    applied_at TIMESTAMP,     -- When the migration was applied
    success BOOLEAN           -- Whether it succeeded
)
```

### Current Migrations

| Version | Description | Status |
|---------|-------------|--------|
| 1 | Create approved_apps table | ✅ Applied |
| 2 | Add revoked_reason column | ✅ Applied |

## Checking Migration Status

Use the provided script to check which migrations have been applied:

```bash
# Load environment variables
export $(cat .env | xargs)

# Check migration status
python scripts/check_migrations.py
```

**Example Output:**
```
✅ Migrations Applied:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Version    Status     Applied At                Description
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1          ✅ Success  2025-10-09 10:30:00       Create approved_apps table
2          ✅ Success  2025-10-09 10:30:01       Add revoked_reason column
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## How Migrations Work

### Automatic Execution

1. **Backend Startup**: When the backend starts, `DeltaManager.__init__()` is called
2. **Verify Prerequisites**: Check that catalog exists (fails if it doesn't)
3. **Create Schema**: Automatically create schema if needed
4. **Load Migrations**: Import from `backend/app/migrations.py`
5. **Validate Schema**: Check versions are sequential, no duplicates
6. **Migration Check**: Query which migrations have been applied
7. **Run Pending**: Only migrations not in `schema_migrations` are executed
8. **Record Results**: Each migration attempt is logged with timestamp and success status

### Prerequisites

⚠️ **IMPORTANT**: The catalog must already exist before running migrations.

**Security Model:**
- ✅ **Schemas**: Automatically created if they don't exist (safe operation)
- ❌ **Catalogs**: Must be pre-created by Unity Catalog admin (security requirement)

**Minimum Required Setup:**
```sql
-- Create catalog (required)
CREATE CATALOG IF NOT EXISTS workspace_guardian;

-- Grant permissions to service principal
GRANT USE CATALOG ON CATALOG workspace_guardian TO `<service_principal>`;
GRANT CREATE SCHEMA ON CATALOG workspace_guardian TO `<service_principal>`;
```

The schema will be automatically created on first backend startup.

## Adding New Migrations

### Step 1: Edit migrations.py

Open `backend/app/migrations.py` and add a new entry to the `migrations` list:

```python
def get_migrations(table_name: str) -> List[Migration]:
    migrations: List[Migration] = [
        # ... existing migrations ...
        {
            'version': 3,  # Next sequential version
            'description': 'Add email_verified column',
            'sql': f"""
            ALTER TABLE {table_name} 
            ADD COLUMNS (email_verified BOOLEAN)
            """
        }
    ]
    return migrations
```

### Step 2: Restart Backend

The migration will run automatically on the next backend startup:

```bash
cd backend
source venv/bin/activate
export $(cat ../.env | xargs)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Step 3: Verify

Check the logs for migration status:

```
======================================================================
🔄 Processing 3 migration(s)...
======================================================================
⏭️  [SKIP] Migration 1 already applied: Create approved_apps table
⏭️  [SKIP] Migration 2 already applied: Add revoked_reason column
🔧 [APPLY] Migration 3: Add email_verified column
✅ [SUCCESS] Migration 3 completed
======================================================================
✅ Migration summary: 2 skipped, 1 applied
======================================================================
```

Or use the check script:

```bash
python scripts/check_migrations.py
```

## Migration Best Practices

### 1. Never Modify Existing Migrations

❌ **DON'T:**
```python
{
    'version': 2,
    'description': 'Add revoked_reason and new_column',  # Changed!
    'sql': f"ALTER TABLE ... ADD COLUMNS (revoked_reason STRING, new_column INT)"
}
```

✅ **DO:**
```python
# Keep version 2 unchanged
{
    'version': 2,
    'description': 'Add revoked_reason column',
    'sql': f"ALTER TABLE ... ADD COLUMNS (revoked_reason STRING)"
},
# Add new migration
{
    'version': 3,
    'description': 'Add new_column',
    'sql': f"ALTER TABLE ... ADD COLUMNS (new_column INT)"
}
```

### 2. Use Sequential Versions

Always use the next sequential version number. The validation will fail if versions are not 1, 2, 3, 4...

### 3. Keep Migrations Small

One logical change per migration:
- ✅ Add single column
- ✅ Add index
- ✅ Modify single constraint
- ❌ Add 5 columns + 3 indexes (split into separate migrations)

### 4. Test Locally First

Before deploying to production:
1. Test migration on local Unity Catalog table
2. Verify with `check_migrations.py`
3. Check data integrity
4. Review logs

### 5. Write Descriptive Names

Good descriptions:
- ✅ "Add email_verified column"
- ✅ "Create index on app_id and workspace_id"
- ✅ "Rename creator to app_creator"

Bad descriptions:
- ❌ "Update table"
- ❌ "Fix schema"
- ❌ "Migration 3"

## Common Migration Patterns

### Add Column

```python
{
    'version': N,
    'description': 'Add column_name column',
    'sql': f"""
    ALTER TABLE {table_name} 
    ADD COLUMNS (column_name STRING)
    """
}
```

### Add Multiple Columns

```python
{
    'version': N,
    'description': 'Add user tracking columns',
    'sql': f"""
    ALTER TABLE {table_name} 
    ADD COLUMNS (
        created_by STRING,
        updated_by STRING,
        deleted_by STRING
    )
    """
}
```

### Modify Column (Requires Data Migration)

```python
{
    'version': N,
    'description': 'Change is_approved to approval_status',
    'sql': f"""
    -- Step 1: Add new column
    ALTER TABLE {table_name} 
    ADD COLUMNS (approval_status STRING);
    
    -- Step 2: Migrate data
    UPDATE {table_name}
    SET approval_status = CASE 
        WHEN is_approved = true THEN 'approved'
        ELSE 'pending'
    END;
    
    -- Step 3: Drop old column (optional, can't undo!)
    -- ALTER TABLE {table_name} DROP COLUMN is_approved;
    """
}
```

## Migration Status Messages

### Status Labels

- ⏭️ **[SKIP]** - Migration already applied, skipping
- 🔧 **[APPLY]** - Currently applying migration
- ✅ **[SUCCESS]** - Migration completed successfully
- ❌ **[FAILED]** - Migration failed with error

### Example Output

```
======================================================================
🚀 Starting migration system...
======================================================================
📊 Using catalog: workspace_guardian, schema: guardian, table: approved_apps
🔍 Verifying catalog: workspace_guardian
✅ Catalog exists: workspace_guardian
🔍 Checking schema: workspace_guardian.guardian
✅ Schema already exists: workspace_guardian.guardian
✅ Migrations table exists: workspace_guardian.guardian.schema_migrations
📋 Applied migrations: [1, 2]
======================================================================
🔄 Processing 2 migration(s)...
======================================================================
⏭️  [SKIP] Migration 1 already applied: Create approved_apps table
⏭️  [SKIP] Migration 2 already applied: Add revoked_reason column
======================================================================
✅ Migration summary: 2 skipped, 0 applied
======================================================================
```

## Troubleshooting

### Migration Failed

**Check the logs:**
```
❌ [FAILED] Migration 3: [Error message]
```

**Check schema_migrations table:**
```bash
python scripts/check_migrations.py
```

Look for failed migrations (success = false).

### Retry Failed Migration

1. Fix the SQL in `backend/app/migrations.py`
2. Delete the failed record from `schema_migrations`:
   ```sql
   DELETE FROM schema_migrations WHERE version = N AND success = false;
   ```
3. Restart backend

### Reset All Migrations (Development Only)

⚠️ **WARNING: This will lose all data!**

```sql
DROP TABLE IF EXISTS {catalog}.{schema}.approved_apps;
DROP TABLE IF EXISTS {catalog}.{schema}.schema_migrations;
```

Then restart the backend to re-run all migrations.

## Validation

The migration system automatically validates:

1. **No Duplicate Versions**: Each version number must be unique
2. **Sequential Versions**: Versions must be 1, 2, 3, 4... (no gaps)
3. **Required Fields**: Each migration must have version, description, and sql
4. **Non-Empty SQL**: SQL statements must not be empty

Validation runs on module import, so errors are caught before the backend starts.

## Production Deployment

### Pre-Deployment Checklist

- [ ] All migrations tested locally
- [ ] Migration versions are sequential
- [ ] No modifications to existing migrations
- [ ] Backup strategy in place
- [ ] Rollback plan documented

### Deployment Process

1. **Backup current state:**
   ```sql
   CREATE TABLE {catalog}.{schema}.approved_apps_backup_20251009
   AS SELECT * FROM {catalog}.{schema}.approved_apps;
   ```

2. **Deploy code** with new migrations

3. **Backend restarts** and runs migrations automatically

4. **Verify migrations:**
   ```bash
   python scripts/check_migrations.py
   ```

5. **Test functionality**

6. **If issues, rollback:**
   ```sql
   RESTORE TABLE {catalog}.{schema}.approved_apps 
   TO VERSION AS OF [previous_version];
   ```

## Migration History

Document major migration changes here:

### 2025-10-09 - Initial Schema (v1)
- Created `approved_apps` table with core columns
- Supports app approval tracking

### 2025-10-09 - Add Revoke Reason (v2)
- Added `revoked_reason` column
- Allows tracking why approvals were revoked

---

## Need Help?

- Review existing migrations in `backend/app/migrations.py`
- Check Unity Catalog documentation
- Use `check_migrations.py` to debug
- Check backend logs for detailed migration execution
