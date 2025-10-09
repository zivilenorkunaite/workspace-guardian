"""FastAPI main application for Workspace Guardian."""
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import logging
import os

from .models import (
    Workspace, DatabricksResource, ResourcesResponse, ApprovalRequest, 
    RevokeRequest, ApprovedResource, ApprovalResponse, RefreshResponse
)
from .databricks_client import DatabricksClient
from .delta_manager import DeltaManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Workspace Guardian",
    description="Monitor and manage Databricks Resources approvals across workspaces",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize clients
try:
    # Detect if running as Databricks App
    is_databricks_app = os.getenv("DATABRICKS_RUNTIME_VERSION") is not None
    
    if is_databricks_app:
        logger.info("🚀 Running as Databricks App - using automatic authentication")
    else:
        logger.info("💻 Running in local development mode")
    
    databricks_client = DatabricksClient()
    
    # Initialize with Unity Catalog schema (catalog.schema)
    # Use APP_CATALOG and APP_SCHEMA env vars with defaults
    delta_catalog = os.getenv("APP_CATALOG", "main")
    delta_schema = os.getenv("APP_SCHEMA", "workspace_guardian")
    
    delta_manager = DeltaManager(catalog=delta_catalog, schema=delta_schema)
    logger.info(f"✅ Initialized with Unity Catalog schema: {delta_catalog}.{delta_schema}")
except Exception as e:
    logger.error(f"❌ Failed to initialize clients: {e}")
    databricks_client = None
    delta_manager = None


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Workspace Guardian",
        "status": "running",
        "version": "1.0.0"
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "databricks_connected": databricks_client is not None,
        "delta_manager_initialized": delta_manager is not None,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/api/workspaces", response_model=List[Workspace])
async def get_workspaces():
    """
    Get list of all accessible Databricks workspaces.
    
    Returns:
        List of workspaces.
    """
    if not databricks_client:
        raise HTTPException(status_code=503, detail="Databricks client not initialized")
    
    try:
        workspaces = databricks_client.get_accessible_workspaces()
        return workspaces
    except Exception as e:
        logger.error(f"Error fetching workspaces: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/apps", response_model=ResourcesResponse)
async def list_apps(workspace_id: Optional[str] = Query(None)):
    """
    List all Databricks apps in a workspace.
    
    Args:
        workspace_id: Optional workspace ID to filter by
        
    Returns:
        List of apps with approval status.
    """
    if not databricks_client or not delta_manager:
        raise HTTPException(status_code=503, detail="Services not initialized")
    
    try:
        # Get all apps from Databricks
        apps_data = databricks_client.list_apps(workspace_id)
        
        # Get approval information (only returns is_approved=true and revoked_date=null)
        approved_apps = delta_manager.get_approved_resources(workspace_id)
        
        # Create lookup dictionary for approvals using resource_id only
        approval_lookup = {app["resource_id"]: app for app in approved_apps}
        
        # Merge app data with approval status
        apps = []
        approved_count = 0
        
        for app_data in apps_data:
            resource_id = app_data["resource_id"]
            
            is_approved = False
            approval_details = None
            
            if resource_id in approval_lookup:
                approval_info = approval_lookup[resource_id]
                # Verify is_approved is True and revoked_date is None
                if approval_info.get("is_approved") and approval_info.get("revoked_date") is None:
                    is_approved = True
                    
                    # Check expiration if set
                    if approval_info.get("expiration_date"):
                        # Parse ISO format date string to timezone-aware datetime
                        exp_date = approval_info["expiration_date"]
                        if isinstance(exp_date, str):
                            from dateutil import parser
                            exp_date = parser.parse(exp_date)
                        
                        # Ensure both are timezone-aware (UTC)
                        now = datetime.now(timezone.utc)
                        if exp_date.tzinfo is None:
                            # exp_date is naive, assume UTC
                            exp_date = exp_date.replace(tzinfo=timezone.utc)
                        
                        if exp_date < now:
                            is_approved = False
                    
                    if is_approved:
                        approved_count += 1
            
            # Merge approval info into resource data
            resource = DatabricksResource(
                **app_data,
                is_approved=is_approved,
                approval_date=approval_info.get("approval_date") if is_approved else None,
                approved_by=approval_info.get("approved_by") if is_approved else None,
                expiration_date=approval_info.get("expiration_date") if is_approved else None,
                justification=approval_info.get("justification") if is_approved else None
            )
            apps.append(resource)
        
        return ResourcesResponse(
            resources=apps,
            workspace_id=workspace_id or "current",
            workspace_name=apps[0].workspace_name if apps else "Unknown"
        )
    except Exception as e:
        logger.error(f"Error listing apps: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/apps/approve")
async def approve_app(request: ApprovalRequest):
    """
    Approve an app with optional expiration date.
    
    Args:
        request: Approval request with app details and justification
        
    Returns:
        Success message.
    """
    logger.info(f"=== APPROVAL REQUEST RECEIVED ===")
    logger.info(f"Resource Name: {request.resource_name}")
    logger.info(f"Resource ID: {request.resource_id}")
    logger.info(f"Workspace: {request.workspace_name} ({request.workspace_id})")
    logger.info(f"Creator: {request.resource_creator}")
    logger.info(f"Approved By: {request.approved_by}")
    logger.info(f"Justification: {request.justification}")
    logger.info(f"Expiration Date: {request.expiration_date}")
    
    if not delta_manager:
        logger.error("Delta manager not initialized")
        raise HTTPException(status_code=503, detail="Delta manager not initialized")
    
    try:
        # Ensure expiration_date is set to midnight UTC if provided
        expiration_date = None
        if request.expiration_date:
            exp = request.expiration_date
            # If timezone-naive, assume UTC
            if exp.tzinfo is None:
                exp = exp.replace(tzinfo=timezone.utc)
            # Set time to 00:00:00
            expiration_date = exp.replace(hour=0, minute=0, second=0, microsecond=0)
            logger.info(f"Normalized expiration date to: {expiration_date}")
        
        approval_data = {
            "resource_name": request.resource_name,
            "resource_id": request.resource_id,
            "workspace_id": request.workspace_id,
            "workspace_name": request.workspace_name,
            "resource_creator": request.resource_creator,
            "approved_by": request.approved_by,
            "approval_date": datetime.now(timezone.utc),
            "expiration_date": expiration_date,
            "justification": request.justification,
        }
        
        logger.info(f"Calling delta_manager.approve_resource()...")
        success = delta_manager.approve_resource(approval_data)
        logger.info(f"Delta manager returned: {success}")
        
        if success:
            logger.info(f"✅ Successfully approved: {request.resource_name}")
            return {
                "status": "success",
                "message": f"Resource {request.resource_name} approved successfully",
                "resource_id": request.resource_id,
                "workspace_id": request.workspace_id
            }
        else:
            logger.error(f"❌ Delta manager returned False for approval")
            raise HTTPException(status_code=500, detail="Failed to approve app")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error approving app: {e}")
        import traceback
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/apps/revoke")
async def revoke_approval(request: RevokeRequest):
    """
    Revoke an app approval.
    
    Args:
        request: Revoke request with app details
        
    Returns:
        Success message.
    """
    if not delta_manager:
        raise HTTPException(status_code=503, detail="Delta manager not initialized")
    
    try:
        success = delta_manager.revoke_approval(
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
            raise HTTPException(status_code=404, detail="Approval not found")
    except Exception as e:
        logger.error(f"Error revoking approval: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/apps/refresh")
async def refresh_apps(workspace_id: Optional[str] = Query(None)):
    """
    Refresh the state of all apps in a workspace.
    
    Args:
        workspace_id: Optional workspace ID to refresh
        
    Returns:
        Success message with count of refreshed apps.
    """
    if not databricks_client:
        raise HTTPException(status_code=503, detail="Databricks client not initialized")
    
    try:
        apps = databricks_client.list_apps(workspace_id)
        
        return {
            "status": "success",
            "message": "Apps refreshed successfully",
            "count": len(apps),
            "workspace_id": workspace_id or "current",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error refreshing apps: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

