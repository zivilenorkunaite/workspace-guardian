"""FastAPI main application for Workspace Guardian (Refactored)."""
import logging
from contextlib import asynccontextmanager
from typing import List, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .models import (
    Workspace, DatabricksResource, ResourcesResponse, ApprovalRequest, 
    RevokeRequest
)
from .services import ApprovalService
from .dependencies import (
    get_databricks_client, get_approval_service, initialize_migrations
)
from .exceptions import (
    WorkspaceGuardianException, ValidationError, ApprovalError, 
    RevocationError, ClientInitializationError
)

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Application lifespan handler
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown."""
    # Startup
    logger.info("=" * 70)
    logger.info(f"🚀 Starting Workspace Guardian v{settings.app_version}")
    logger.info("=" * 70)
    
    if settings.is_databricks_app:
        logger.info("📍 Running as Databricks App - using automatic authentication")
    else:
        logger.info("💻 Running in local development mode")
    
    try:
        # Initialize database migrations
        initialize_migrations()
    except Exception as e:
        logger.error(f"❌ Failed to initialize migrations: {e}")
        # Don't fail startup, but log the error
    
    logger.info(f"✅ Workspace Guardian initialized successfully")
    logger.info(f"📊 Using catalog: {settings.app_catalog}.{settings.app_schema}")
    logger.info("=" * 70)
    
    yield
    
    # Shutdown
    logger.info("👋 Shutting down Workspace Guardian")


# Initialize FastAPI app
app = FastAPI(
    title="Workspace Guardian",
    description="Monitor and manage Databricks Resources approvals across workspaces",
    version=settings.app_version,
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(ValidationError)
async def validation_error_handler(request, exc: ValidationError):
    """Handle validation errors."""
    return HTTPException(status_code=400, detail=str(exc))


@app.exception_handler(ApprovalError)
async def approval_error_handler(request, exc: ApprovalError):
    """Handle approval errors."""
    return HTTPException(status_code=500, detail=str(exc))


@app.exception_handler(RevocationError)
async def revocation_error_handler(request, exc: RevocationError):
    """Handle revocation errors."""
    return HTTPException(status_code=500, detail=str(exc))


@app.exception_handler(ClientInitializationError)
async def client_init_error_handler(request, exc: ClientInitializationError):
    """Handle client initialization errors."""
    return HTTPException(status_code=503, detail=str(exc))


@app.exception_handler(WorkspaceGuardianException)
async def generic_error_handler(request, exc: WorkspaceGuardianException):
    """Handle generic Workspace Guardian errors."""
    return HTTPException(status_code=500, detail=str(exc))


# Routes
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Workspace Guardian",
        "status": "running",
        "version": settings.app_version
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    try:
        client = get_databricks_client()
        client_available = True
    except Exception:
        client_available = False
    
    return {
        "status": "healthy",
        "databricks_connected": client_available,
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.app_version
    }


@app.get("/api/workspaces", response_model=List[Workspace])
async def get_workspaces():
    """
    Get list of all accessible Databricks workspaces.
    
    Returns:
        List of workspaces
    """
    try:
        client = get_databricks_client()
        workspaces = client.get_accessible_workspaces()
        return workspaces
    except Exception as e:
        logger.error(f"Error fetching workspaces: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/resources", response_model=ResourcesResponse)
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


@app.post("/api/resources/approve")
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
        success = service.approve_resource(
            resource_name=request.resource_name,
            resource_id=request.resource_id,
            workspace_id=request.workspace_id,
            workspace_name=request.workspace_name,
            resource_creator=request.resource_creator,
            approved_by=request.approved_by,
            justification=request.justification,
            expiration_date=request.expiration_date
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


@app.post("/api/resources/revoke")
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


@app.post("/api/resources/refresh")
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

@app.get("/api/apps", response_model=ResourcesResponse, deprecated=True)
async def list_apps_deprecated(
    workspace_id: Optional[str] = Query(None),
    service: ApprovalService = Depends(get_approval_service)
):
    """
    [DEPRECATED] Use /api/resources instead.
    List all Databricks resources with approval status.
    """
    return await list_resources(workspace_id, service)


@app.post("/api/apps/approve", deprecated=True)
async def approve_app_deprecated(
    request: ApprovalRequest,
    service: ApprovalService = Depends(get_approval_service)
):
    """
    [DEPRECATED] Use /api/resources/approve instead.
    Approve a resource with optional expiration date.
    """
    return await approve_resource(request, service)


@app.post("/api/apps/revoke", deprecated=True)
async def revoke_app_deprecated(
    request: RevokeRequest,
    service: ApprovalService = Depends(get_approval_service)
):
    """
    [DEPRECATED] Use /api/resources/revoke instead.
    Revoke a resource approval.
    """
    return await revoke_resource(request, service)


@app.post("/api/apps/refresh", deprecated=True)
async def refresh_apps_deprecated(
    workspace_id: Optional[str] = Query(None),
    service: ApprovalService = Depends(get_approval_service)
):
    """
    [DEPRECATED] Use /api/resources/refresh instead.
    Refresh resources from Databricks.
    """
    return await refresh_resources(workspace_id, service)

