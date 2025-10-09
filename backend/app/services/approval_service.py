"""Business logic for resource approvals."""
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from dateutil import parser

from ..clients import DatabricksClient
from ..repositories.approval_repository import ApprovalRepository
from ..models import DatabricksResource
from ..exceptions import ApprovalError, RevocationError, ValidationError

logger = logging.getLogger(__name__)


class ApprovalService:
    """Handles business logic for resource approvals."""
    
    def __init__(
        self, 
        databricks_client: DatabricksClient,
        approval_repository: ApprovalRepository
    ):
        """
        Initialize approval service.
        
        Args:
            databricks_client: Databricks client instance
            approval_repository: Approval repository instance
        """
        self.client = databricks_client
        self.repo = approval_repository
    
    def list_resources_with_approvals(
        self, 
        workspace_id: Optional[str] = None
    ) -> List[DatabricksResource]:
        """
        List all resources with their approval status.
        
        Args:
            workspace_id: Optional workspace ID to filter by
            
        Returns:
            List of resources with approval information
        """
        # Get all resources from Databricks
        resources_data = self.client.list_apps(workspace_id)
        
        # Get approval information
        approved_resources = self.repo.get_approved_resources(workspace_id)
        
        # Create lookup dictionary for approvals using resource_id
        approval_lookup = {res["resource_id"]: res for res in approved_resources}
        
        # Merge resource data with approval status
        resources = []
        
        for resource_data in resources_data:
            resource_id = resource_data["resource_id"]
            
            is_approved = False
            approval_info = approval_lookup.get(resource_id)
            
            if approval_info:
                # Verify is_approved is True and revoked_date is None
                if approval_info.get("is_approved") and approval_info.get("revoked_date") is None:
                    is_approved = True
                    
                    # Check expiration if set
                    if approval_info.get("expiration_date"):
                        exp_date = approval_info["expiration_date"]
                        if isinstance(exp_date, str):
                            exp_date = parser.parse(exp_date)
                        
                        # Ensure both are timezone-aware (UTC)
                        now = datetime.now(timezone.utc)
                        if exp_date.tzinfo is None:
                            exp_date = exp_date.replace(tzinfo=timezone.utc)
                        
                        if exp_date < now:
                            is_approved = False
            
            # Create resource with approval info
            resource = DatabricksResource(
                **resource_data,
                is_approved=is_approved,
                approval_date=approval_info.get("approval_date") if is_approved else None,
                approved_by=approval_info.get("approved_by") if is_approved else None,
                expiration_date=approval_info.get("expiration_date") if is_approved else None,
                justification=approval_info.get("justification") if is_approved else None
            )
            resources.append(resource)
        
        return resources
    
    def approve_resource(
        self,
        resource_name: str,
        resource_id: str,
        workspace_id: str,
        workspace_name: str,
        resource_creator: str,
        approved_by: str,
        justification: str,
        expiration_date: Optional[datetime] = None
    ) -> bool:
        """
        Approve a resource.
        
        Args:
            resource_name: Name of the resource
            resource_id: ID of the resource
            workspace_id: Workspace ID
            workspace_name: Workspace name
            resource_creator: Creator of the resource
            approved_by: User approving the resource
            justification: Reason for approval
            expiration_date: Optional expiration date
            
        Returns:
            True if successful
            
        Raises:
            ApprovalError: If approval fails
            ValidationError: If validation fails
        """
        # Validate inputs
        if not resource_name or not resource_id:
            raise ValidationError("Resource name and ID are required")
        
        if not justification or len(justification.strip()) < 10:
            raise ValidationError("Justification must be at least 10 characters")
        
        # Normalize expiration date if provided
        normalized_exp_date = None
        if expiration_date:
            if expiration_date.tzinfo is None:
                expiration_date = expiration_date.replace(tzinfo=timezone.utc)
            # Set time to 00:00:00
            normalized_exp_date = expiration_date.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Prepare approval data
        approval_data = {
            "resource_name": resource_name,
            "resource_id": resource_id,
            "workspace_id": workspace_id,
            "workspace_name": workspace_name,
            "resource_creator": resource_creator,
            "approved_by": approved_by,
            "approval_date": datetime.now(timezone.utc),
            "expiration_date": normalized_exp_date,
            "justification": justification,
        }
        
        logger.info(f"📝 Approving resource: {resource_name} (ID: {resource_id})")
        
        # Approve via repository
        success = self.repo.approve_resource(approval_data)
        
        if success:
            logger.info(f"✅ Successfully approved resource: {resource_name}")
        else:
            logger.error(f"❌ Failed to approve resource: {resource_name}")
        
        return success
    
    def revoke_approval(
        self,
        resource_id: str,
        workspace_id: str,
        revoked_by: str,
        revoked_reason: str
    ) -> bool:
        """
        Revoke a resource approval.
        
        Args:
            resource_id: ID of the resource
            workspace_id: Workspace ID
            revoked_by: User revoking the approval
            revoked_reason: Reason for revocation
            
        Returns:
            True if successful
            
        Raises:
            RevocationError: If revocation fails
            ValidationError: If validation fails
        """
        # Validate inputs
        if not resource_id or not workspace_id:
            raise ValidationError("Resource ID and workspace ID are required")
        
        if not revoked_reason or len(revoked_reason.strip()) < 10:
            raise ValidationError("Revocation reason must be at least 10 characters")
        
        logger.info(f"📝 Revoking approval for resource ID: {resource_id}")
        
        # Revoke via repository
        success = self.repo.revoke_approval(
            resource_id=resource_id,
            workspace_id=workspace_id,
            revoked_by=revoked_by,
            revoked_reason=revoked_reason
        )
        
        if success:
            logger.info(f"✅ Successfully revoked approval for resource ID: {resource_id}")
        else:
            logger.error(f"❌ Failed to revoke approval for resource ID: {resource_id}")
        
        return success
    
    def refresh_resources(self, workspace_id: Optional[str] = None) -> int:
        """
        Refresh resources from Databricks (no-op, just returns count).
        
        Args:
            workspace_id: Optional workspace ID
            
        Returns:
            Number of resources synced
        """
        resources = self.client.list_apps(workspace_id)
        return len(resources)

