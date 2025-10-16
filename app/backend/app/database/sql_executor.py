"""SQL execution layer for Databricks SQL Warehouse."""
import logging
from typing import List, Dict, Any, Optional
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementState

from ..config import settings
from ..exceptions import DatabaseError

logger = logging.getLogger(__name__)


class SQLExecutor:
    """Executes SQL statements against Databricks SQL Warehouse."""
    
    def __init__(self, client: WorkspaceClient):
        """
        Initialize SQL executor.
        
        Args:
            client: Databricks WorkspaceClient instance
        """
        self.client = client
        self.warehouse_id = settings.databricks_warehouse_id
    
    def execute(self, sql: str) -> List[Dict[str, Any]]:
        """
        Execute SQL statement and return results.
        
        Args:
            sql: SQL statement to execute
            
        Returns:
            List of result rows as dictionaries
            
        Raises:
            DatabaseError: If execution fails
        """
        try:
            logger.debug(f"Executing SQL on warehouse {self.warehouse_id}: {sql[:100]}...")
            result = self.client.statement_execution.execute_statement(
                warehouse_id=self.warehouse_id,
                statement=sql,
                wait_timeout="30s"
            )
            
            # Check if execution failed
            if result.status.state == StatementState.FAILED:
                error_msg = result.status.error.message if result.status.error else "Unknown error"
                raise DatabaseError(f"SQL execution failed: {error_msg}")
            
            if result.status.state == StatementState.SUCCEEDED:
                return self._parse_results(result)
            
            return []
            
        except DatabaseError:
            raise
        except Exception as e:
            error_msg = str(e)
            
            # Don't log expected errors as ERROR
            expected_errors = [
                'ALREADY_EXISTS',
                'FIELD_ALREADY_EXISTS',
                'TABLE_OR_VIEW_NOT_FOUND',
                'SCHEMA_NOT_FOUND'
            ]
            
            is_expected = any(err in error_msg for err in expected_errors)
            
            if is_expected:
                logger.debug(f"SQL execution encountered expected condition: {error_msg[:200]}")
            else:
                logger.error(f"SQL execution failed: {e}")
            
            raise DatabaseError(f"SQL execution error: {error_msg}", details={"sql": sql[:200]})
    
    def _parse_results(self, result) -> List[Dict[str, Any]]:
        """
        Parse SQL execution results into list of dictionaries.
        
        Args:
            result: Statement execution result object
            
        Returns:
            List of rows as dictionaries
        """
        rows = []
        
        logger.info(f"SQL succeeded, parsing results...")
        logger.info(f"Has manifest: {result.manifest is not None}")
        logger.info(f"Has result: {result.result is not None}")
        
        if not (result.manifest and result.manifest.schema and result.result):
            return rows
        
        if not hasattr(result.result, 'data_array') or not result.result.data_array:
            return rows
        
        logger.info(f"Data array length: {len(result.result.data_array)}")
        
        # Extract column names and types
        columns = [col.name for col in result.manifest.schema.columns]
        column_types = {col.name: str(col.type_name) for col in result.manifest.schema.columns}
        
        # Parse each row
        for row_data in result.result.data_array:
            row = {}
            for col_name, value in zip(columns, row_data):
                # Convert boolean strings to actual booleans
                col_type = column_types.get(col_name, '')
                if 'BOOLEAN' in col_type and isinstance(value, str):
                    row[col_name] = value.lower() == 'true'
                else:
                    row[col_name] = value
            rows.append(row)
        
        logger.info(f"Parsed {len(rows)} rows from SQL result")
        return rows

