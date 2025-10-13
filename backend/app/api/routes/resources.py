"""Resource listing and management endpoints."""
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Depends

from ...models import ResourcesResponse
from ...services import ApprovalService
from ...dependencies import get_approval_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/resources", tags=["resources"])


@router.get("", response_model=ResourcesResponse)
async def list_resources(
    workspace_id: Optional[str] = Query(None),
    service: ApprovalService = Depends(get_approval_service)
):
    """
    List all Databricks resources with approval status.
    
    Args:
        workspace_id: Optional workspace ID to filter by
        service: Approval service (injected)
        
    Returns:
        Resources with approval information
    """
    try:
        resources = service.list_resources_with_approvals(workspace_id)
        
        return ResourcesResponse(
            resources=resources,
            workspace_id=workspace_id or "current",
            workspace_name=resources[0].workspace_name if resources else "Unknown"
        )
    except Exception as e:
        logger.error(f"Error listing resources: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/refresh")
async def refresh_resources(
    workspace_id: Optional[str] = Query(None),
    service: ApprovalService = Depends(get_approval_service)
):
    """
    Refresh resources from Databricks.
    
    Args:
        workspace_id: Optional workspace ID
        service: Approval service (injected)
        
    Returns:
        Sync status
    """
    try:
        count = service.refresh_resources(workspace_id)
        
        return {
            "status": "success",
            "message": f"Synced {count} resources",
            "resources_synced": count
        }
    except Exception as e:
        logger.error(f"Error refreshing resources: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# BACKWARD COMPATIBILITY ROUTES (deprecated, use /api/resources/* instead)
# ============================================================================

@router.get("/apps", response_model=ResourcesResponse, deprecated=True, include_in_schema=False)
async def list_apps_deprecated(
    workspace_id: Optional[str] = Query(None),
    service: ApprovalService = Depends(get_approval_service)
):
    """
    [DEPRECATED] Use /api/resources instead.
    List all Databricks resources with approval status.
    """
    return await list_resources(workspace_id, service)


@router.post("/apps/refresh", deprecated=True, include_in_schema=False)
async def refresh_apps_deprecated(
    workspace_id: Optional[str] = Query(None),
    service: ApprovalService = Depends(get_approval_service)
):
    """
    [DEPRECATED] Use /api/resources/refresh instead.
    Refresh resources from Databricks.
    """
    return await refresh_resources(workspace_id, service)

