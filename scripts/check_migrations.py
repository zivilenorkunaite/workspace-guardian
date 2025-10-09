#!/usr/bin/env python3
"""
Check migration status for the Workspace Guardian Delta tables.
"""
import os
import sys
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from databricks.sdk import WorkspaceClient


def check_migrations():
    """Check and display migration status."""
    # Load environment variables
    host = os.getenv('DATABRICKS_HOST')
    token = os.getenv('DATABRICKS_TOKEN')
    warehouse_id = os.getenv('DATABRICKS_WAREHOUSE_ID')
    catalog = os.getenv('APP_CATALOG', 'main')
    schema = os.getenv('APP_SCHEMA', 'workspace_guardian')
    
    if not all([host, token, warehouse_id]):
        print("❌ Missing required environment variables:")
        print("   DATABRICKS_HOST, DATABRICKS_TOKEN, DATABRICKS_WAREHOUSE_ID")
        return
    
    # Build table names
    approved_resources_table = f"{catalog}.{schema}.approved_resources"
    migrations_table = f"{catalog}.{schema}.migration_definitions"
    
    print(f"🔍 Checking migrations for schema: {catalog}.{schema}")
    print(f"📊 Approved resources table: {approved_resources_table}")
    print(f"📊 Migration definitions table: {migrations_table}")
    print()
    
    # Initialize client
    client = WorkspaceClient(host=host, token=token)
    
    try:
        # Check if migrations table exists
        sql = f"""
        SELECT 
            version, 
            description, 
            status,
            applied_at, 
            applied_by,
            execution_time_seconds,
            error_message,
            source_version,
            migration_type
        FROM {migrations_table} 
        ORDER BY version
        """
        
        response = client.statement_execution.execute_statement(
            warehouse_id=warehouse_id,
            statement=sql,
            wait_timeout="30s"
        )
        
        if response.status.state.value == 'SUCCEEDED':
            # Parse results
            if response.result and response.result.data_array:
                print("✅ Migrations Applied:")
                print("━" * 80)
                print(f"{'Version':<10} {'Status':<10} {'Applied At':<25} {'Description':<35}")
                print("━" * 80)
                
                for row in response.result.data_array:
                    version = row[0]
                    description = row[1]
                    applied_at = row[2]
                    success = row[3]
                    
                    status = "✅ Success" if success == 'true' else "❌ Failed"
                    
                    print(f"{version:<10} {status:<10} {applied_at:<25} {description:<35}")
                
                print("━" * 80)
            else:
                print("⚠️  No migrations found (table exists but is empty)")
        else:
            print(f"❌ Query failed: {response.status.state}")
            
    except Exception as e:
        if "TABLE_OR_VIEW_NOT_FOUND" in str(e):
            print("⚠️  Migrations table does not exist yet")
            print("   (Will be created on first backend startup)")
        else:
            print(f"❌ Error: {e}")
    
    print()
    
    # Check if main table exists
    try:
        desc_sql = f"DESCRIBE TABLE {approved_resources_table}"
        response = client.statement_execution.execute_statement(
            warehouse_id=warehouse_id,
            statement=desc_sql,
            wait_timeout="30s"
        )
        
        if response.status.state.value == 'SUCCEEDED':
            print(f"✅ Table exists: {approved_resources_table}")
            print()
            print("Columns:")
            print("━" * 60)
            
            if response.result and response.result.data_array:
                for row in response.result.data_array:
                    col_name = row[0]
                    col_type = row[1]
                    print(f"  {col_name:<25} {col_type}")
            
            print("━" * 60)
    except Exception as e:
        if "TABLE_OR_VIEW_NOT_FOUND" in str(e):
            print(f"⚠️  Table does not exist yet: {approved_resources_table}")
            print("   (Will be created on first backend startup)")
        else:
            print(f"❌ Error checking table: {e}")


if __name__ == "__main__":
    check_migrations()


