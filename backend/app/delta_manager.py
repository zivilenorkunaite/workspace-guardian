"""Manager for Delta table operations using Unity Catalog."""
import os
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
import logging
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementState

from app.migrations import get_migrations, validate_migrations, get_migration_definitions_ddl

# PySpark imports - will only work in Databricks environment
try:
    from pyspark.sql import SparkSession
    from pyspark.sql.functions import col, lit, current_timestamp
    from delta import configure_spark_with_delta_pip
    SPARK_AVAILABLE = True
except ImportError:
    SPARK_AVAILABLE = False

logger = logging.getLogger(__name__)


class DeltaManager:
    """Manager for Delta Lake operations using Unity Catalog for workspace guardian schema."""
    
    def __init__(self, catalog: Optional[str] = None, schema: Optional[str] = None):
        """
        Initialize Delta manager for workspace guardian schema.
        
        Args:
            catalog: Catalog name (uses env APP_CATALOG or defaults to 'main')
            schema: Schema name (uses env APP_SCHEMA or defaults to 'workspace_guardian')
        """
        # Parse from env or use defaults
        self.catalog = catalog or os.getenv("APP_CATALOG", "main")
        self.schema = schema or os.getenv("APP_SCHEMA", "workspace_guardian")
        
        # Define application tables
        self.approved_apps_table = f"{self.catalog}.{self.schema}.approved_apps"
        
        logger.info(f"🏗️  Initializing workspace guardian schema: {self.catalog}.{self.schema}")
        logger.info(f"📊 Main table: {self.approved_apps_table}")
        
        # Initialize Databricks client for SQL execution
        try:
            is_databricks_app = os.getenv("DATABRICKS_RUNTIME_VERSION") is not None
            
            if is_databricks_app:
                # Databricks App - automatic authentication
                self.client = WorkspaceClient()
                logger.info("Using Databricks App authentication")
            else:
                # Local development - explicit credentials
                host = os.getenv("DATABRICKS_HOST")
                token = os.getenv("DATABRICKS_TOKEN")
                if host and token:
                    self.client = WorkspaceClient(host=host, token=token)
                    logger.info("Using local development credentials")
                else:
                    self.client = None
                    logger.warning("Databricks client credentials not provided")
            
            if self.client:
                logger.info(f"✅ Databricks client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Databricks client: {e}")
            self.client = None
        
        if not SPARK_AVAILABLE:
            logger.info(
                "PySpark not available - Using Databricks SQL API for Delta operations. "
                "This works for both local development and Databricks deployment."
            )
            self.spark = None
            self._ensure_table_exists()
            return
        
        # Initialize Spark session with Unity Catalog support
        builder = SparkSession.builder \
            .appName("WorkspaceGuardian") \
            .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
            .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
        
        self.spark = configure_spark_with_delta_pip(builder).getOrCreate()
        
        # Initialize tables if they don't exist (via migrations)
        self._initialize_table()
    
    def _get_catalog_schema(self):
        """Get catalog and schema for migrations."""
        logger.info(f"📊 Managing schema: {self.catalog}.{self.schema}")
        return self.catalog, self.schema
    
    def _verify_catalog_and_ensure_schema(self, catalog, schema):
        """Verify catalog exists (must be pre-created), create schema if needed."""
        # Step 1: Verify catalog exists (SECURITY: do not create catalogs)
        logger.info(f"🔍 Verifying catalog: {catalog}")
        try:
            self._execute_sql(f"USE CATALOG {catalog}")
            logger.info(f"✅ Catalog exists: {catalog}")
        except Exception as e:
            logger.error(f"❌ Catalog does not exist: {catalog}")
            logger.error(f"   SECURITY: Catalogs must be pre-created by Unity Catalog admin")
            logger.error(f"   Run this SQL: CREATE CATALOG IF NOT EXISTS {catalog};")
            raise Exception(f"Catalog {catalog} does not exist. Please create it first.")
        
        # Step 2: Create schema if it doesn't exist (safe operation)
        logger.info(f"🔍 Checking schema: {catalog}.{schema}")
        try:
            # After USE CATALOG, use schema name without catalog prefix for USE SCHEMA
            self._execute_sql(f"USE SCHEMA {schema}")
            logger.info(f"✅ Schema already exists: {catalog}.{schema}")
        except Exception as e:
            # Schema doesn't exist, create it with fully qualified name
            logger.info(f"📝 Schema does not exist, creating: {catalog}.{schema}")
            # IMPORTANT: Use fully qualified name to avoid empty catalog errors
            self._execute_sql(f"CREATE SCHEMA IF NOT EXISTS {catalog}.{schema}")
            logger.info(f"✅ Schema created successfully: {catalog}.{schema}")
    
    def _ensure_migration_definitions_table(self, catalog, schema):
        """
        Create migration_definitions table - THE FIRST TABLE CREATED.
        This stores all migration metadata with OEM standard fields.
        """
        table_name = f"{catalog}.{schema}.migration_definitions"
        
        logger.info(f"📋 Ensuring migration_definitions table exists: {table_name}")
        
        try:
            # Get DDL from migrations module
            ddl = get_migration_definitions_ddl(catalog, schema)
            self._execute_sql(ddl)
            logger.info(f"✅ Migration definitions table exists: {table_name}")
            return table_name
        except Exception as e:
            logger.error(f"Failed to create migration_definitions table: {e}")
            return None
    
    def _get_applied_migrations(self, migrations_table):
        """Get list of applied migration versions from migration_definitions table."""
        try:
            result = self._execute_sql(f"""
                SELECT version, description, applied_at, status 
                FROM {migrations_table} 
                WHERE status = 'applied' 
                ORDER BY version
            """)
            versions = [row['version'] for row in result]
            logger.info(f"📋 Applied migrations: {versions}")
            return set(versions)
        except Exception as e:
            logger.warning(f"Could not read migrations (table may be empty): {e}")
            return set()
    
    def _record_migration(self, migrations_table, migration: Dict[str, Any], 
                         status='applied', execution_time=0.0, error_message=None):
        """Record a migration in the migration_definitions table with ORM fields."""
        try:
            import hashlib
            
            version = migration['version']
            description = migration['description']
            sql_statement = migration['sql']
            
            now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            
            # Calculate checksum for integrity verification
            checksum = hashlib.sha256(sql_statement.encode()).hexdigest()
            
            # Get current user/service principal
            current_user = os.getenv('DATABRICKS_USER', 'system')
            
            # Escape single quotes in strings
            description_escaped = description.replace("'", "''")
            sql_escaped = sql_statement.replace("'", "''")
            error_escaped = error_message.replace("'", "''") if error_message else None
            
            insert_sql = f"""
                INSERT INTO {migrations_table} 
                (
                    version, description, sql_statement, checksum,
                    status, applied_at, execution_time_seconds, error_message,
                    created_at, updated_at, created_by, updated_by
                )
                VALUES (
                    {version}, '{description_escaped}', '{sql_escaped}', '{checksum}',
                    '{status}', TIMESTAMP '{now}', {execution_time}, 
                    {f"'{error_escaped}'" if error_escaped else 'NULL'},
                    TIMESTAMP '{now}', TIMESTAMP '{now}', '{current_user}', '{current_user}'
                )
            """
            
            self._execute_sql(insert_sql)
            logger.info(f"✅ Recorded migration {version}")
        except Exception as e:
            logger.error(f"Failed to record migration: {e}")
    
    def _run_migrations(self):
        """Run all pending schema-wide migrations in order."""
        logger.info("=" * 70)
        logger.info("🚀 Starting schema-wide migration system...")
        logger.info("=" * 70)
        
        catalog, schema = self._get_catalog_schema()
        
        # Verify catalog exists, create schema if needed
        self._verify_catalog_and_ensure_schema(catalog, schema)
        
        # Create migration_definitions table FIRST - this is the foundation
        migrations_table = self._ensure_migration_definitions_table(catalog, schema)
        if not migrations_table:
            logger.error("Failed to create migration_definitions table - cannot proceed")
            return
            
        applied = self._get_applied_migrations(migrations_table)
        
        # Load schema-wide migrations from migrations module
        migrations = get_migrations(catalog, schema)
        
        # Validate migrations before running
        validate_migrations(migrations)
        
        logger.info("=" * 70)
        logger.info(f"🔄 Processing {len(migrations)} migration(s)...")
        logger.info("=" * 70)
        
        pending_count = 0
        skipped_count = 0
        
        for migration in migrations:
            version = migration['version']
            
            if version in applied:
                logger.info(f"⏭️  [SKIP] Migration {version} already applied: {migration['description']}")
                skipped_count += 1
                continue
            
            pending_count += 1
            logger.info(f"🔧 [APPLY] Migration {version}: {migration['description']}")
            logger.debug(f"   SQL: {migration['sql'][:100]}...")
            
            start_time = datetime.now(timezone.utc)
            try:
                self._execute_sql(migration['sql'])
                execution_time = (datetime.now(timezone.utc) - start_time).total_seconds()
                
                self._record_migration(
                    migrations_table, migration, 
                    status='applied', execution_time=execution_time
                )
                
                logger.info(f"✅ [SUCCESS] Migration {version} completed in {execution_time:.2f}s")
            except Exception as e:
                execution_time = (datetime.now(timezone.utc) - start_time).total_seconds()
                error_msg = str(e)
                
                # Check if error is because column/table already exists
                # This is expected when re-running migrations, so handle gracefully
                if 'ALREADY_EXISTS' in error_msg or 'FIELD_ALREADY_EXISTS' in error_msg or 'already exists' in error_msg.lower():
                    logger.info(f"✅ [SUCCESS] Migration {version} target already exists")
                    self._record_migration(
                        migrations_table, migration,
                        status='applied', execution_time=execution_time,
                        error_message='Target already exists (expected)'
                    )
                else:
                    # Actual error - log and fail
                    logger.error(f"❌ [FAILED] Migration {version}: {error_msg}")
                    self._record_migration(
                        migrations_table, migration,
                        status='failed', execution_time=execution_time,
                        error_message=error_msg
                    )
                    # Only raise if it's a CREATE TABLE error (critical)
                    if 'CREATE TABLE' in migration['sql']:
                        raise
        
        logger.info("=" * 70)
        logger.info(f"✅ Migration summary: {skipped_count} skipped, {pending_count} applied")
        logger.info("=" * 70)
    
    def _ensure_table_exists(self):
        """Ensure the approved apps table exists using migrations system."""
        if not self.client:
            logger.warning("Cannot create table - Databricks client not available")
            return
            
        try:
            self._run_migrations()
        except Exception as e:
            logger.error(f"Error running migrations: {e}")
            raise
    
    def _execute_sql(self, sql: str) -> List[Dict[str, Any]]:
        """Execute SQL using Databricks SQL API."""
        if not self.client:
            raise Exception("Databricks client not available")
        
        warehouse_id = os.getenv("DATABRICKS_WAREHOUSE_ID")
        if not warehouse_id:
            raise Exception("DATABRICKS_WAREHOUSE_ID must be set in environment variables")
        
        try:
            # Use SQL warehouse to execute query
            logger.debug(f"Executing SQL on warehouse {warehouse_id}: {sql[:100]}...")
            result = self.client.statement_execution.execute_statement(
                warehouse_id=warehouse_id,
                statement=sql,
                wait_timeout="30s"
            )
            
            # Check if execution failed
            if result.status.state == StatementState.FAILED:
                error_msg = result.status.error.message if result.status.error else "Unknown error"
                raise Exception(f"SQL execution failed: {error_msg}")
            
            if result.status.state == StatementState.SUCCEEDED:
                # Parse results if available
                rows = []
                logger.info(f"SQL succeeded, parsing results...")
                logger.info(f"Has manifest: {result.manifest is not None}")
                logger.info(f"Has result: {result.result is not None}")
                
                if result.manifest and result.manifest.schema and result.result and hasattr(result.result, 'data_array'):
                    logger.info(f"Has data_array: {result.result.data_array is not None if hasattr(result.result, 'data_array') else False}")
                    if result.result.data_array:
                        logger.info(f"Data array length: {len(result.result.data_array)}")
                        columns = [col.name for col in result.manifest.schema.columns]
                        column_types = {col.name: str(col.type_name) for col in result.manifest.schema.columns}
                        
                        for row_data in result.result.data_array:
                            row = {}
                            for i, (col_name, value) in enumerate(zip(columns, row_data)):
                                # Convert boolean strings to actual booleans
                                col_type = column_types.get(col_name, '')
                                if 'BOOLEAN' in col_type and isinstance(value, str):
                                    row[col_name] = value.lower() == 'true'
                                else:
                                    row[col_name] = value
                            rows.append(row)
                        logger.info(f"Parsed {len(rows)} rows from SQL result")
                return rows
            return []
        except Exception as e:
            # Don't log expected migration check errors as ERROR
            error_msg = str(e)
            expected_errors = [
                'ALREADY_EXISTS',
                'FIELD_ALREADY_EXISTS',
                'TABLE_OR_VIEW_NOT_FOUND',
                'SCHEMA_NOT_FOUND'
            ]
            
            is_expected = any(err in error_msg for err in expected_errors)
            
            if is_expected:
                # These are expected when checking if resources exist
                logger.debug(f"SQL execution encountered expected condition: {error_msg[:200]}")
            else:
                # Unexpected errors
                logger.error(f"SQL execution failed: {e}")
            raise
    
    def _initialize_table(self):
        """Create the approved apps Delta table in Unity Catalog if it doesn't exist."""
        if not SPARK_AVAILABLE or self.spark is None:
            logger.info("Using SQL API for table initialization")
            self._ensure_table_exists()
            return
            
        try:
            # Create catalog if it doesn't exist (may require permissions)
            try:
                self.spark.sql(f"CREATE CATALOG IF NOT EXISTS {self.catalog}")
                logger.info(f"Catalog {self.catalog} is available")
            except Exception as e:
                logger.warning(f"Could not create catalog {self.catalog}: {e}")
            
            # Create schema if it doesn't exist
            try:
                self.spark.sql(f"CREATE SCHEMA IF NOT EXISTS {self.catalog}.{self.schema}")
                logger.info(f"Schema {self.catalog}.{self.schema} is available")
            except Exception as e:
                logger.warning(f"Could not create schema: {e}")
            
            # Check if table exists
            table_exists = self.spark.catalog.tableExists(self.approved_apps_table)
            
            if table_exists:
                logger.info(f"Unity Catalog table exists: {self.approved_apps_table}")
            else:
                # Create table using SQL
                logger.info(f"Creating Unity Catalog table: {self.approved_apps_table}")
                
                create_table_sql = f"""
                CREATE TABLE IF NOT EXISTS {self.approved_apps_table} (
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
                    revoked_reason STRING COMMENT 'Reason for revocation',
                    updated_at TIMESTAMP COMMENT 'Last update timestamp'
                )
                USING DELTA
                COMMENT 'Approved Databricks apps with audit trail'
                """
                
                self.spark.sql(create_table_sql)
                logger.info(f"Unity Catalog table created successfully: {self.approved_apps_table}")
        except Exception as e:
            logger.error(f"Error initializing Unity Catalog table: {e}")
            raise
    
    def get_approved_apps(self, workspace_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all approved apps, optionally filtered by workspace.
        
        Args:
            workspace_id: Optional workspace ID to filter by
            
        Returns:
            List of approved app dictionaries.
        """
        if not SPARK_AVAILABLE or self.spark is None:
            # Use Databricks SQL API
            if not self.client:
                logger.warning("Cannot get approved apps - Databricks client not available")
                return []
            
            try:
                # Get apps where is_approved=true AND revoked_date IS NULL
                sql = f"SELECT * FROM {self.approved_apps_table} WHERE is_approved = true AND revoked_date IS NULL"
                if workspace_id:
                    sql += f" AND workspace_id = '{workspace_id}'"
                
                logger.info(f"Getting approved apps with SQL: {sql}")
                results = self._execute_sql(sql)
                logger.info(f"SQL returned {len(results)} results")
                
                # Convert to expected format
                apps = []
                for row in results:
                    apps.append({
                        "app_name": row.get("app_name"),
                        "app_id": row.get("app_id"),
                        "workspace_id": row.get("workspace_id"),
                        "workspace_name": row.get("workspace_name"),
                        "app_creator": row.get("app_creator"),
                        "approved_by": row.get("approved_by"),
                        "approval_date": row.get("approval_date"),
                        "expiration_date": row.get("expiration_date"),
                        "justification": row.get("justification"),
                        "is_approved": row.get("is_approved"),
                        "revoked_date": row.get("revoked_date"),
                        "revoked_by": row.get("revoked_by"),
                        "revoked_reason": row.get("revoked_reason"),
                    })
                logger.info(f"Returning {len(apps)} approved apps")
                return apps
            except Exception as e:
                logger.error(f"Error getting approved apps: {e}")
                import traceback
                logger.error(traceback.format_exc())
                return []
            
        try:
            df = self.spark.table(self.approved_apps_table)
            
            if workspace_id:
                df = df.filter(col("workspace_id") == workspace_id)
            
            # Convert to list of dictionaries
            return [row.asDict() for row in df.collect()]
        except Exception as e:
            logger.error(f"Error reading approved apps: {e}")
            return []
    
    def approve_app(self, approval_data: Dict[str, Any]) -> bool:
        """
        Add or update an app approval.
        
        Args:
            approval_data: Dictionary with approval information
            
        Returns:
            True if successful, False otherwise.
        """
        logger.info(f"🔵 Delta Manager: approve_app() called")
        logger.info(f"🔵 Approval data keys: {approval_data.keys()}")
        
        # Prepare data
        data = {
            "app_name": approval_data["app_name"],
            "app_id": approval_data["app_id"],
            "workspace_id": approval_data["workspace_id"],
            "workspace_name": approval_data["workspace_name"],
            "app_creator": approval_data["app_creator"],
            "approved_by": approval_data["approved_by"],
            "approval_date": approval_data.get("approval_date", datetime.now(timezone.utc)),
            "expiration_date": approval_data.get("expiration_date"),
            "justification": approval_data["justification"],
            "is_approved": True,
            "revoked_date": None,
            "revoked_by": None,
            "updated_at": datetime.now(timezone.utc)
        }
        
        logger.info(f"🔵 Prepared data: app_id={data['app_id']}, workspace_id={data['workspace_id']}")
        logger.info(f"🔵 Approved apps table: {self.approved_apps_table}")
        
        if not SPARK_AVAILABLE or self.spark is None:
            logger.info(f"🔵 Using Databricks SQL API (Spark not available)")
            # Use Databricks SQL API
            if not self.client:
                logger.warning("Cannot approve app - Databricks client not available")
                return False
            
            try:
                logger.info(f"🔵 Preparing SQL MERGE statement...")
                # Format timestamps for SQL (ensure UTC)
                approval_date = data["approval_date"]
                if approval_date.tzinfo is None:
                    approval_date = approval_date.replace(tzinfo=timezone.utc)
                approval_date_str = approval_date.strftime("%Y-%m-%d %H:%M:%S")
                
                if data["expiration_date"]:
                    exp_date = data["expiration_date"]
                    if exp_date.tzinfo is None:
                        exp_date = exp_date.replace(tzinfo=timezone.utc)
                    # Ensure time is 00:00:00
                    exp_date = exp_date.replace(hour=0, minute=0, second=0, microsecond=0)
                    expiration_date_str = f"'{exp_date.strftime('%Y-%m-%d %H:%M:%S')}'"
                else:
                    expiration_date_str = "NULL"
                
                updated_at = data["updated_at"]
                if updated_at.tzinfo is None:
                    updated_at = updated_at.replace(tzinfo=timezone.utc)
                updated_at_str = updated_at.strftime("%Y-%m-%d %H:%M:%S")
                
                # Use MERGE for upsert
                merge_sql = f"""
                MERGE INTO {self.approved_apps_table} AS target
                USING (
                    SELECT 
                        '{data["app_name"]}' as app_name,
                        '{data["app_id"]}' as app_id,
                        '{data["workspace_id"]}' as workspace_id,
                        '{data["workspace_name"]}' as workspace_name,
                        '{data["app_creator"]}' as app_creator,
                        '{data["approved_by"]}' as approved_by,
                        TIMESTAMP '{approval_date_str}' as approval_date,
                        {expiration_date_str} as expiration_date,
                        '{data["justification"].replace("'", "''")}' as justification,
                        true as is_approved,
                        NULL as revoked_date,
                        NULL as revoked_by,
                        NULL as revoked_reason,
                        TIMESTAMP '{updated_at_str}' as updated_at
                ) AS source
                ON target.app_id = source.app_id AND target.workspace_id = source.workspace_id
                WHEN MATCHED THEN UPDATE SET *
                WHEN NOT MATCHED THEN INSERT *
                """
                
                logger.info(f"🔵 Executing MERGE for app: {data['app_name']}")
                logger.info(f"🔵 MERGE SQL:\n{merge_sql}")
                
                result = self._execute_sql(merge_sql)
                logger.info(f"🔵 SQL execution result: {result}")
                logger.info(f"✅ Successfully approved app {data['app_name']} via SQL API")
                return True
            except Exception as e:
                logger.error(f"❌ Error approving app via SQL API: {e}")
                import traceback
                logger.error(f"❌ Traceback: {traceback.format_exc()}")
                return False
        
        # Use PySpark
        try:
            # Create DataFrame
            new_approval_df = self.spark.createDataFrame([data])
            
            # Register temporary view for merge
            new_approval_df.createOrReplaceTempView("new_approval")
            
            # Use Delta MERGE for upsert operation
            merge_sql = f"""
                MERGE INTO {self.approved_apps_table} AS target
                USING new_approval AS source
                ON target.app_id = source.app_id AND target.workspace_id = source.workspace_id
                WHEN MATCHED THEN UPDATE SET *
                WHEN NOT MATCHED THEN INSERT *
            """
            
            self.spark.sql(merge_sql)
            logger.info(f"Approved app {data['app_name']} in workspace {data['workspace_id']}")
            return True
        except Exception as e:
            logger.error(f"Error approving app: {e}")
            return False
    
    def revoke_approval(self, app_id: str, workspace_id: str, revoked_by: str, revoked_reason: str) -> bool:
        """
        Revoke an app approval (marks as not approved but keeps in table).
        
        Args:
            app_id: ID of the app
            workspace_id: ID of the workspace
            revoked_by: User who revoked the approval
            revoked_reason: Reason for revocation
            
        Returns:
            True if successful, False otherwise.
        """
        if not SPARK_AVAILABLE or self.spark is None:
            # Use Databricks SQL API
            if not self.client:
                logger.warning("Cannot revoke approval - Databricks client not available")
                return False
            
            try:
                revoked_timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
                # Escape single quotes in reason
                escaped_reason = revoked_reason.replace("'", "''")
                update_sql = f"""
                    UPDATE {self.approved_apps_table}
                    SET 
                        is_approved = FALSE,
                        revoked_date = TIMESTAMP '{revoked_timestamp}',
                        revoked_by = '{revoked_by}',
                        revoked_reason = '{escaped_reason}',
                        updated_at = CURRENT_TIMESTAMP()
                    WHERE app_id = '{app_id}' AND workspace_id = '{workspace_id}'
                """
                
                self._execute_sql(update_sql)
                logger.info(f"Revoked approval for app {app_id} via SQL API")
                return True
            except Exception as e:
                logger.error(f"Error revoking approval via SQL API: {e}")
                return False
        
        # Use PySpark
        try:
            # Check if approval exists
            check_sql = f"""
                SELECT COUNT(*) as count 
                FROM {self.approved_apps_table}
                WHERE app_id = '{app_id}' AND workspace_id = '{workspace_id}'
            """
            count = self.spark.sql(check_sql).first()['count']
            
            if count == 0:
                logger.warning(f"No approval found for app {app_id} in workspace {workspace_id}")
                return False
            
            # Update using SQL for atomic operation
            revoked_timestamp = datetime.now(timezone.utc)
            # Escape single quotes in reason
            escaped_reason = revoked_reason.replace("'", "''")
            update_sql = f"""
                    UPDATE {self.approved_apps_table}
                SET 
                    is_approved = FALSE,
                    revoked_date = TIMESTAMP '{revoked_timestamp.strftime('%Y-%m-%d %H:%M:%S')}',
                    revoked_by = '{revoked_by}',
                    revoked_reason = '{escaped_reason}',
                    updated_at = CURRENT_TIMESTAMP()
                WHERE app_id = '{app_id}' AND workspace_id = '{workspace_id}'
            """
            
            self.spark.sql(update_sql)
            logger.info(f"Revoked approval for app {app_id} in workspace {workspace_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error revoking approval: {e}")
            return False
    
    def is_app_approved(self, app_id: str, workspace_id: str) -> tuple[bool, Optional[Dict[str, Any]]]:
        """
        Check if an app is approved and get approval details.
        
        Args:
            app_id: ID of the app
            workspace_id: ID of the workspace
            
        Returns:
            Tuple of (is_approved, approval_details)
        """
        if not SPARK_AVAILABLE or self.spark is None:
            logger.warning("Cannot check approval status - PySpark not available")
            return False, None
            
        try:
            df = self.spark.table(self.approved_apps_table)
            
            approval = df.filter(
                (col("app_id") == app_id) & 
                (col("workspace_id") == workspace_id) & 
                (col("is_approved") == True)
            )
            
            if approval.count() > 0:
                approval_dict = approval.first().asDict()
                
                # Check if expired
                if approval_dict.get("expiration_date"):
                    if approval_dict["expiration_date"] < datetime.utcnow():
                        return False, None
                
                return True, approval_dict
            
            return False, None
        except Exception as e:
            logger.error(f"Error checking approval status: {e}")
            return False, None

