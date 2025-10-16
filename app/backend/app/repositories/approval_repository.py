"""Repository for managing resource approvals."""
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from ..database.sql_executor import SQLExecutor
from ..config import settings
from ..exceptions import DatabaseError, ApprovalError, RevocationError

logger = logging.getLogger(__name__)


class ApprovalRepository:
    """Handles CRUD operations for resource approvals."""
    
    def __init__(self, sql_executor: SQLExecutor, catalog: Optional[str] = None, schema: Optional[str] = None):
        """
        Initialize approval repository.
        
        Args:
            sql_executor: SQL executor instance
            catalog: Catalog name (defaults to settings)
            schema: Schema name (defaults to settings)
        """
        self.executor = sql_executor
        self.catalog = catalog or settings.app_catalog
        self.schema = schema or settings.app_schema
        self.approved_resources_table = f"{self.catalog}.{self.schema}.approved_resources"
        
        logger.info(f"📊 Approval repository initialized for table: {self.approved_resources_table}")
    
    def get_approved_resources(self, workspace_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all approved resources, optionally filtered by workspace.
        
        Args:
            workspace_id: Optional workspace ID to filter by
            
        Returns:
            List of approved resource dictionaries
        """
        try:
            # Get resources where is_approved=true AND revoked_date IS NULL
            sql = f"""
                SELECT * FROM {self.approved_resources_table} 
                WHERE is_approved = true AND revoked_date IS NULL
            """
            if workspace_id:
                sql += f" AND workspace_id = '{workspace_id}'"
            
            logger.info(f"Getting approved resources with SQL: {sql}")
            results = self.executor.execute(sql)
            logger.info(f"SQL returned {len(results)} results")
            
            # Convert to expected format
            resources = []
            for row in results:
                resources.append({
                    "resource_name": row.get("resource_name"),
                    "resource_id": row.get("resource_id"),
                    "workspace_id": row.get("workspace_id"),
                    "workspace_name": row.get("workspace_name"),
                    "resource_creator": row.get("resource_creator"),
                    "approved_by": row.get("approved_by"),
                    "approval_date": row.get("approval_date"),
                    "expiration_date": row.get("expiration_date"),
                    "justification": row.get("justification"),
                    "is_approved": row.get("is_approved"),
                    "revoked_date": row.get("revoked_date"),
                    "revoked_by": row.get("revoked_by"),
                    "revoked_reason": row.get("revoked_reason"),
                })
            
            logger.info(f"Returning {len(resources)} approved resources")
            return resources
            
        except DatabaseError:
            raise
        except Exception as e:
            logger.error(f"Error getting approved resources: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise DatabaseError(f"Failed to get approved resources: {e}")
    
    def approve_resource(self, approval_data: Dict[str, Any]) -> bool:
        """
        Add or update a resource approval.
        
        Args:
            approval_data: Dictionary with approval information
            
        Returns:
            True if successful
            
        Raises:
            ApprovalError: If approval fails
        """
        logger.info(f"🔵 Approval Repository: approve_resource() called")
        logger.info(f"🔵 Approval data keys: {approval_data.keys()}")
        
        try:
            # Prepare data
            data = {
                "resource_name": approval_data["resource_name"],
                "resource_id": approval_data["resource_id"],
                "workspace_id": approval_data["workspace_id"],
                "workspace_name": approval_data["workspace_name"],
                "resource_creator": approval_data["resource_creator"],
                "approved_by": approval_data["approved_by"],
                "approval_date": approval_data.get("approval_date", datetime.now(timezone.utc)),
                "expiration_date": approval_data.get("expiration_date"),
                "justification": approval_data["justification"],
            }
            
            logger.info(f"🔵 Prepared data: resource_id={data['resource_id']}, workspace_id={data['workspace_id']}")
            
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
            
            updated_at = datetime.now(timezone.utc)
            updated_at_str = updated_at.strftime("%Y-%m-%d %H:%M:%S")
            
            # Use MERGE for upsert
            merge_sql = f"""
            MERGE INTO {self.approved_resources_table} AS target
            USING (
                SELECT 
                    '{data["resource_name"]}' as resource_name,
                    '{data["resource_id"]}' as resource_id,
                    '{data["workspace_id"]}' as workspace_id,
                    '{data["workspace_name"]}' as workspace_name,
                    '{data["resource_creator"]}' as resource_creator,
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
            ON target.resource_id = source.resource_id AND target.workspace_id = source.workspace_id
            WHEN MATCHED THEN UPDATE SET *
            WHEN NOT MATCHED THEN INSERT *
            """
            
            logger.info(f"🔵 Executing MERGE for resource: {data['resource_name']}")
            logger.debug(f"🔵 MERGE SQL:\n{merge_sql}")
            
            self.executor.execute(merge_sql)
            logger.info(f"✅ Successfully approved resource {data['resource_name']}")
            return True
            
        except DatabaseError:
            raise ApprovalError(f"Failed to approve resource: {approval_data.get('resource_name')}")
        except Exception as e:
            logger.error(f"❌ Error approving resource: {e}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            raise ApprovalError(f"Failed to approve resource: {e}")
    
    def revoke_approval(
        self, 
        resource_id: str, 
        workspace_id: str, 
        revoked_by: str, 
        revoked_reason: str
    ) -> bool:
        """
        Revoke a resource approval (marks as not approved but keeps in table).
        
        Args:
            resource_id: ID of the resource
            workspace_id: ID of the workspace
            revoked_by: User who revoked the approval
            revoked_reason: Reason for revocation
            
        Returns:
            True if successful
            
        Raises:
            RevocationError: If revocation fails
        """
        try:
            revoked_timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
            # Escape single quotes in reason
            escaped_reason = revoked_reason.replace("'", "''")
            
            update_sql = f"""
                UPDATE {self.approved_resources_table}
                SET 
                    is_approved = FALSE,
                    revoked_date = TIMESTAMP '{revoked_timestamp}',
                    revoked_by = '{revoked_by}',
                    revoked_reason = '{escaped_reason}',
                    updated_at = CURRENT_TIMESTAMP()
                WHERE resource_id = '{resource_id}' AND workspace_id = '{workspace_id}'
            """
            
            self.executor.execute(update_sql)
            logger.info(f"✅ Revoked approval for resource {resource_id}")
            return True
            
        except DatabaseError:
            raise RevocationError(f"Failed to revoke approval for resource: {resource_id}")
        except Exception as e:
            logger.error(f"Error revoking approval: {e}")
            raise RevocationError(f"Failed to revoke approval: {e}")
    
    def is_resource_approved(
        self, 
        resource_id: str, 
        workspace_id: str
    ) -> tuple[bool, Optional[Dict[str, Any]]]:
        """
        Check if a resource is approved and get approval details.
        
        Args:
            resource_id: ID of the resource
            workspace_id: ID of the workspace
            
        Returns:
            Tuple of (is_approved, approval_details)
        """
        try:
            sql = f"""
                SELECT * FROM {self.approved_resources_table}
                WHERE resource_id = '{resource_id}' 
                AND workspace_id = '{workspace_id}' 
                AND is_approved = true
                AND revoked_date IS NULL
            """
            
            results = self.executor.execute(sql)
            
            if results:
                approval = results[0]
                
                # Check if expired
                if approval.get("expiration_date"):
                    exp_date = approval["expiration_date"]
                    if isinstance(exp_date, str):
                        from dateutil import parser
                        exp_date = parser.parse(exp_date)
                    
                    if exp_date < datetime.now(timezone.utc):
                        return False, None
                
                return True, approval
            
            return False, None
            
        except Exception as e:
            logger.error(f"Error checking approval status: {e}")
            return False, None

