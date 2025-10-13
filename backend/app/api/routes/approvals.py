"""Approval and revocation endpoints."""
import logging

from fastapi import APIRouter, HTTPException, Depends

from ...models import ApprovalRequest, RevokeRequest
from ...services import ApprovalService
from ...dependencies import get_approval_service
from ...exceptions import ValidationError, ApprovalError, RevocationError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/resources", tags=["approvals"])


@router.post("/approve")
async def approve_resource(
    request: ApprovalRequest,
    service: ApprovalService = Depends(get_approval_service)
):
    """
    Approve a resource with optional expiration date.
    
    Args:
        request: Approval request with resource details
        service: Approval service (injected)
        
    Returns:
        Success message
    """
    logger.info(f"=== APPROVAL REQUEST RECEIVED ===")
    logger.info(f"Resource: {request.resource_name} (ID: {request.resource_id})")
    logger.info(f"Workspace: {request.workspace_name} ({request.workspace_id})")
    logger.info(f"Approved by: {request.approved_by}")
    
    try:
        # Parse expiration_date string to datetime if provided
        expiration_datetime = None
        if request.expiration_date:
            from datetime import datetime as dt
            from dateutil import parser
            expiration_datetime = parser.parse(request.expiration_date)
        
        success = service.approve_resource(
            resource_name=request.resource_name,
            resource_id=request.resource_id,
            workspace_id=request.workspace_id,
            workspace_name=request.workspace_name,
            resource_creator=request.resource_creator,
            approved_by=request.approved_by,
            justification=request.justification,
            expiration_date=expiration_datetime
        )
        
        if success:
            logger.info(f"✅ Successfully approved: {request.resource_name}")
            return {
                "status": "success",
                "message": f"Resource {request.resource_name} approved successfully",
                "resource_id": request.resource_id,
                "workspace_id": request.workspace_id
            }
        else:
            raise ApprovalError("Failed to approve resource")
            
    except (ValidationError, ApprovalError):
        raise
    except Exception as e:
        logger.error(f"❌ Error approving resource: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/revoke")
async def revoke_resource(
    request: RevokeRequest,
    service: ApprovalService = Depends(get_approval_service)
):
    """
    Revoke a resource approval.
    
    Args:
        request: Revoke request with resource details
        service: Approval service (injected)
        
    Returns:
        Success message
    """
    try:
        success = service.revoke_approval(
            resource_id=request.resource_id,
            workspace_id=request.workspace_id,
            revoked_by=request.revoked_by,
            revoked_reason=request.revoked_reason
        )
        
        if success:
            return {
                "status": "success",
                "message": f"Resource {request.resource_name} approval revoked successfully",
                "resource_id": request.resource_id,
                "workspace_id": request.workspace_id
            }
        else:
            raise RevocationError("Approval not found")
            
    except (ValidationError, RevocationError):
        raise
    except Exception as e:
        logger.error(f"Error revoking approval: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# BACKWARD COMPATIBILITY ROUTES (deprecated, use /api/resources/* instead)
# ============================================================================

@router.post("/apps/approve", deprecated=True, include_in_schema=False)
async def approve_app_deprecated(
    request: ApprovalRequest,
    service: ApprovalService = Depends(get_approval_service)
):
    """
    [DEPRECATED] Use /api/resources/approve instead.
    Approve a resource with optional expiration date.
    """
    return await approve_resource(request, service)


@router.post("/apps/revoke", deprecated=True, include_in_schema=False)
async def revoke_app_deprecated(
    request: RevokeRequest,
    service: ApprovalService = Depends(get_approval_service)
):
    """
    [DEPRECATED] Use /api/resources/revoke instead.
    Revoke a resource approval.
    """
    return await revoke_resource(request, service)

