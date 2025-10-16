"""Database migration management."""
import hashlib
import logging
import os
from datetime import datetime, timezone
from typing import Dict, Any, Set, Optional

from .sql_executor import SQLExecutor
from .migrations import get_migrations, validate_migrations, get_migration_definitions_ddl
from ..config import settings
from ..exceptions import MigrationError, DatabaseError

logger = logging.getLogger(__name__)


class MigrationManager:
    """Manages database schema migrations."""
    
    def __init__(self, sql_executor: SQLExecutor, catalog: Optional[str] = None, schema: Optional[str] = None):
        """
        Initialize migration manager.
        
        Args:
            sql_executor: SQL executor instance
            catalog: Catalog name (defaults to settings)
            schema: Schema name (defaults to settings)
        """
        self.executor = sql_executor
        self.catalog = catalog or settings.app_catalog
        self.schema = schema or settings.app_schema
        
        logger.info(f"🏗️  Initializing migration manager for: {self.catalog}.{self.schema}")
    
    def run_migrations(self) -> None:
        """
        Run all pending schema migrations.
        
        Raises:
            MigrationError: If migrations fail
        """
        logger.info("=" * 70)
        logger.info("🚀 Starting schema-wide migration system...")
        logger.info("=" * 70)
        
        try:
            # Step 1: Verify catalog exists, create schema if needed
            self._verify_catalog_and_ensure_schema()
            
            # Step 2: Create migration_definitions table FIRST
            migrations_table = self._ensure_migration_definitions_table()
            if not migrations_table:
                raise MigrationError("Failed to create migration_definitions table")
            
            # Step 3: Get applied migrations
            applied = self._get_applied_migrations(migrations_table)
            
            # Step 4: Load and validate migrations
            migrations = get_migrations(self.catalog, self.schema)
            validate_migrations(migrations)
            
            # Early exit: Check if all migrations are already applied
            pending_migrations = [m for m in migrations if m['version'] not in applied]
            if not pending_migrations:
                logger.info(f"✅ All {len(migrations)} migration(s) already applied - nothing to do")
                logger.info("=" * 70)
                logger.info("✅ Migration system completed (no changes needed)")
                logger.info("=" * 70)
                return
            
            # Step 5: Apply pending migrations
            self._apply_migrations(migrations, applied, migrations_table)
            
            logger.info("=" * 70)
            logger.info("✅ Migration system completed successfully")
            logger.info("=" * 70)
            
        except Exception as e:
            logger.error(f"❌ Migration system failed: {e}")
            raise MigrationError(f"Migration failed: {e}")
    
    def _verify_catalog_and_ensure_schema(self) -> None:
        """
        Verify catalog exists (must be pre-created), create schema if needed.
        
        Raises:
            MigrationError: If catalog doesn't exist
        """
        # Step 1: Verify catalog exists (SECURITY: do not create catalogs)
        logger.info(f"🔍 Verifying catalog: {self.catalog}")
        try:
            self.executor.execute(f"USE CATALOG {self.catalog}")
            logger.info(f"✅ Catalog exists: {self.catalog}")
        except Exception as e:
            logger.error(f"❌ Catalog does not exist: {self.catalog}")
            logger.error(f"   SECURITY: Catalogs must be pre-created by Unity Catalog admin")
            logger.error(f"   Run this SQL: CREATE CATALOG IF NOT EXISTS {self.catalog};")
            raise MigrationError(
                f"Catalog {self.catalog} does not exist. Please create it first.",
                details={"catalog": self.catalog}
            )
        
        # Step 2: Check if schema exists (using fully qualified name)
        logger.info(f"🔍 Checking schema: {self.catalog}.{self.schema}")
        try:
            # Check schema existence using DESCRIBE (more reliable than USE)
            result = self.executor.execute(f"DESCRIBE SCHEMA {self.catalog}.{self.schema}")
            if result:
                logger.info(f"✅ Schema already exists: {self.catalog}.{self.schema}")
            else:
                raise Exception("Schema not found")
        except Exception as e:
            # Schema doesn't exist, create it with fully qualified name
            logger.info(f"📝 Schema does not exist, creating: {self.catalog}.{self.schema}")
            logger.debug(f"   Schema check error (expected if new): {e}")
            self.executor.execute(f"CREATE SCHEMA IF NOT EXISTS {self.catalog}.{self.schema}")
            logger.info(f"✅ Schema created successfully: {self.catalog}.{self.schema}")
    
    def _ensure_migration_definitions_table(self) -> str:
        """
        Create migration_definitions table - THE FIRST TABLE CREATED.
        
        Returns:
            Table name
            
        Raises:
            MigrationError: If table creation fails
        """
        table_name = f"{self.catalog}.{self.schema}.migration_definitions"
        
        logger.info(f"📋 Ensuring migration_definitions table exists: {table_name}")
        
        try:
            ddl = get_migration_definitions_ddl(self.catalog, self.schema)
            self.executor.execute(ddl)
            logger.info(f"✅ Migration definitions table ready: {table_name}")
            
            # Verify table is accessible by counting rows
            try:
                count_result = self.executor.execute(f"SELECT COUNT(*) as cnt FROM {table_name}")
                row_count = count_result[0]['cnt'] if count_result else 0
                logger.info(f"📊 Migration table contains {row_count} record(s)")
            except Exception as count_err:
                logger.warning(f"Could not count migration records: {count_err}")
            
            return table_name
        except Exception as e:
            logger.error(f"Failed to create migration_definitions table: {e}")
            raise MigrationError(f"Failed to create migration_definitions table: {e}")
    
    def _get_applied_migrations(self, migrations_table: str) -> Set[int]:
        """
        Get list of applied migration versions.
        
        Args:
            migrations_table: Migration definitions table name
            
        Returns:
            Set of applied migration versions
        """
        try:
            # First, verify table exists by describing it
            logger.info(f"🔍 Checking if migration_definitions table has data...")
            
            result = self.executor.execute(f"""
                SELECT version, description, applied_at, status 
                FROM {migrations_table} 
                WHERE status = 'applied' 
                ORDER BY version
            """)
            
            if not result:
                logger.info(f"📋 No applied migrations found (table is empty)")
                return set()
            
            # CRITICAL: Convert version to int to ensure type consistency
            # Database may return version as string, long, or other numeric types
            versions = []
            for row in result:
                try:
                    version = int(row['version'])
                    versions.append(version)
                except (ValueError, TypeError) as e:
                    logger.warning(f"Invalid version in migration record: {row.get('version')} - {e}")
            
            logger.info(f"📋 Found {len(versions)} applied migration(s): {sorted(versions)}")
            logger.debug(f"   Applied versions (type={type(versions[0]) if versions else 'N/A'}): {versions}")
            return set(versions)
            
        except Exception as e:
            error_msg = str(e).lower()
            
            # Check if it's a "table doesn't exist" error
            if any(x in error_msg for x in ['not found', 'does not exist', 'table_or_view_not_found']):
                logger.info(f"📋 Migration table doesn't exist yet (first run) - will create it")
                return set()
            else:
                # Unexpected error - log it prominently
                logger.error(f"❌ Error reading migration_definitions table: {e}")
                logger.error(f"   Table: {migrations_table}")
                logger.error(f"   This may indicate a permissions or schema issue")
                return set()
    
    def _apply_migrations(
        self, 
        migrations: list, 
        applied: Set[int], 
        migrations_table: str
    ) -> None:
        """
        Apply pending migrations.
        
        Args:
            migrations: List of migration definitions
            applied: Set of already applied migration versions
            migrations_table: Migration definitions table name
        """
        logger.info("=" * 70)
        logger.info(f"🔄 Processing {len(migrations)} migration(s)...")
        logger.info(f"   Applied versions: {sorted(applied) if applied else '(none)'}")
        logger.info("=" * 70)
        
        pending_count = 0
        skipped_count = 0
        
        for migration in migrations:
            version = migration['version']
            
            # Debug logging for version comparison
            logger.debug(f"Comparing migration version {version} (type={type(version)}) against applied: {applied}")
            
            if version in applied:
                logger.info(f"⏭️  [SKIP] Migration {version} already applied: {migration['description']}")
                skipped_count += 1
                continue
            
            pending_count += 1
            logger.info(f"🔧 [APPLY] Migration {version}: {migration['description']}")
            logger.debug(f"   SQL: {migration['sql'][:100]}...")
            
            start_time = datetime.now(timezone.utc)
            try:
                self.executor.execute(migration['sql'])
                execution_time = (datetime.now(timezone.utc) - start_time).total_seconds()
                
                self._record_migration(
                    migrations_table, migration, 
                    status='applied', execution_time=execution_time
                )
                
                logger.info(f"✅ [SUCCESS] Migration {version} completed in {execution_time:.2f}s")
                
            except DatabaseError as e:
                execution_time = (datetime.now(timezone.utc) - start_time).total_seconds()
                error_msg = str(e)
                
                # Check if error is because resource already exists
                if any(x in error_msg for x in ['ALREADY_EXISTS', 'FIELD_ALREADY_EXISTS', 'already exists']):
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
                        raise MigrationError(f"Critical migration failed: {error_msg}")
        
        logger.info("=" * 70)
        logger.info(f"✅ Migration summary: {skipped_count} skipped, {pending_count} applied")
        logger.info("=" * 70)
    
    def _record_migration(
        self, 
        migrations_table: str, 
        migration: Dict[str, Any], 
        status: str = 'applied', 
        execution_time: float = 0.0, 
        error_message: Optional[str] = None
    ) -> None:
        """
        Record a migration in the migration_definitions table.
        
        Args:
            migrations_table: Migration definitions table name
            migration: Migration definition
            status: Migration status ('applied' or 'failed')
            execution_time: Execution time in seconds
            error_message: Error message if failed
        """
        try:
            version = migration['version']
            description = migration['description']
            sql_statement = migration['sql']
            
            # CRITICAL: Check if this version already exists to prevent duplicates
            #existing = self.executor.execute(f"""
            #    SELECT version FROM {migrations_table} 
            #    WHERE version = {version}
            #    LIMIT 1
            #""")
            
            #if existing and len(existing) > 0:
            #    logger.warning(f"⚠️  Migration version {version} already recorded in table - skipping duplicate insert")
            #    return
            
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
            
            self.executor.execute(insert_sql)
            logger.info(f"✅ Recorded migration {version}")
            
        except Exception as e:
            logger.error(f"Failed to record migration: {e}")

