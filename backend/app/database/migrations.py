"""
Database migrations for Workspace Guardian.

This module defines all schema migrations in a versioned, idempotent format.
Migrations are tracked in the migration_definitions table.
"""
from typing import List, Dict, Any


def get_migration_definitions_ddl(catalog: str, schema: str) -> str:
    """
    Get DDL for migration_definitions table - THE FIRST TABLE CREATED.
    
    This table tracks all migrations applied to the schema with ORM-style fields.
    
    Args:
        catalog: Unity Catalog name
        schema: Schema name
        
    Returns:
        CREATE TABLE statement for migration_definitions
    """
    table_name = f"{catalog}.{schema}.migration_definitions"
    
    return f"""
    CREATE TABLE IF NOT EXISTS {table_name} (
        version INT NOT NULL COMMENT 'Migration version number (must be unique)',
        description STRING NOT NULL COMMENT 'Human-readable migration description',
        sql_statement STRING NOT NULL COMMENT 'SQL statement executed',
        checksum STRING NOT NULL COMMENT 'SHA-256 checksum of SQL statement',
        status STRING NOT NULL COMMENT 'Migration status: applied, failed',
        applied_at TIMESTAMP COMMENT 'When migration was applied',
        execution_time_seconds DOUBLE COMMENT 'How long migration took to execute',
        error_message STRING COMMENT 'Error message if migration failed',
        created_at TIMESTAMP NOT NULL COMMENT 'Record creation timestamp',
        updated_at TIMESTAMP NOT NULL COMMENT 'Record last update timestamp',
        created_by STRING NOT NULL COMMENT 'User/service who created record',
        updated_by STRING NOT NULL COMMENT 'User/service who last updated record'
    )
    USING DELTA
    COMMENT 'Migration tracking table - records all schema changes. Version uniqueness enforced by application logic.'
    """


def get_migrations(catalog: str, schema: str) -> List[Dict[str, Any]]:
    """
    Get all migrations for the workspace guardian schema.
    
    Migrations are:
    - Versioned: Each has a unique version number
    - Idempotent: Safe to run multiple times (using IF NOT EXISTS, IF EXISTS)
    - Ordered: Applied in version order
    - Tracked: Recorded in migration_definitions table
    
    Args:
        catalog: Unity Catalog name
        schema: Schema name
        
    Returns:
        List of migration dictionaries with version, description, and SQL
    """
    migrations = [
        # ============================================================================
        # Migration 1: Create approved_resources table
        # ============================================================================
        {
            "version": 1,
            "description": "Create approved_resources table for resource approval tracking",
            "sql": f"""
                CREATE TABLE IF NOT EXISTS {catalog}.{schema}.approved_resources (
                    resource_name STRING COMMENT 'Name of the resource',
                    resource_id STRING COMMENT 'Unique resource identifier',
                    workspace_id STRING COMMENT 'Databricks workspace ID',
                    workspace_name STRING COMMENT 'Workspace display name',
                    resource_creator STRING COMMENT 'User who created the resource',
                    approved_by STRING COMMENT 'User who approved the resource',
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
            """
        },
        
        # ============================================================================
        # Migration 2: Add revoked_reason column
        # ============================================================================
        {
            "version": 2,
            "description": "Add revoked_reason column to track why approvals were revoked",
            "sql": f"""
                ALTER TABLE {catalog}.{schema}.approved_resources 
                ADD COLUMN revoked_reason STRING 
                COMMENT 'Reason for revocation'
            """
        },
        
        # ============================================================================
        # Future migrations go here...
        # ============================================================================
        # Example:
        # {
        #     "version": 3,
        #     "description": "Add new column or table",
        #     "sql": f"""
        #         ALTER TABLE {catalog}.{schema}.approved_resources
        #         ADD COLUMN IF NOT EXISTS new_field STRING
        #     """
        # },
    ]
    
    return migrations


def validate_migrations(migrations: List[Dict[str, Any]]) -> None:
    """
    Validate that migrations are properly formatted and versioned.
    
    Args:
        migrations: List of migration dictionaries
        
    Raises:
        ValueError: If migrations are invalid
    """
    if not migrations:
        raise ValueError("No migrations defined")
    
    # Check for required fields
    for migration in migrations:
        if "version" not in migration:
            raise ValueError(f"Migration missing 'version' field: {migration}")
        if "description" not in migration:
            raise ValueError(f"Migration missing 'description' field: {migration}")
        if "sql" not in migration:
            raise ValueError(f"Migration missing 'sql' field: {migration}")
    
    # Check for unique, sequential versions
    versions = [m["version"] for m in migrations]
    if len(versions) != len(set(versions)):
        raise ValueError(f"Duplicate migration versions found: {versions}")
    
    sorted_versions = sorted(versions)
    if sorted_versions != list(range(1, len(versions) + 1)):
        raise ValueError(f"Migration versions must be sequential starting from 1. Got: {sorted_versions}")
    
    # Check that migrations are ordered by version
    if versions != sorted_versions:
        raise ValueError(f"Migrations must be ordered by version. Expected: {sorted_versions}, Got: {versions}")

