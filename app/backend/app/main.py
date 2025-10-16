"""FastAPI main application for Workspace Guardian."""
import logging
from contextlib import asynccontextmanager
from typing import Optional
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from .config import settings
from .dependencies import initialize_migrations, get_approval_service
from .models import ResourcesResponse, ApprovalRequest, RevokeRequest
from .services import ApprovalService
from .exceptions import (
    WorkspaceGuardianException, ValidationError, ApprovalError, 
    RevocationError, ClientInitializationError
)
from .api.routes import health, workspaces, resources, approvals

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
    
    # Check static files (logging only - routes registered at module level)
    static_dir = Path(__file__).parent.parent.parent / "frontend" / "dist"
    logger.info(f"🔍 Checking static files at startup...")
    logger.info(f"📂 Static directory path: {static_dir}")
    logger.info(f"📂 Static directory exists: {static_dir.exists()}")
    if static_dir.exists():
        logger.info(f"📂 Static directory contents: {list(static_dir.iterdir())}")
        index_html = static_dir / "index.html"
        logger.info(f"📄 index.html exists: {index_html.exists()}")
        if index_html.exists():
            logger.info(f"📄 index.html size: {index_html.stat().st_size} bytes")
        else:
            logger.warning(f"⚠️  index.html not found!")
    else:
        logger.warning(f"⚠️  Static directory not found!")
    
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


# Include routers
app.include_router(health.router)
app.include_router(workspaces.router)
app.include_router(resources.router)
app.include_router(approvals.router)


# ============================================================================
# BACKWARD COMPATIBILITY ROUTES (deprecated, use /api/resources/* instead)
# ============================================================================
# These routes maintain compatibility with the old API endpoints

@app.get("/api/apps", response_model=ResourcesResponse, deprecated=True, include_in_schema=False)
async def list_apps_deprecated(
    workspace_id: Optional[str] = Query(None),
    service: ApprovalService = Depends(get_approval_service)
):
    """[DEPRECATED] Use /api/resources instead."""
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


@app.post("/api/apps/approve", deprecated=True, include_in_schema=False)
async def approve_app_deprecated(
    request: ApprovalRequest,
    service: ApprovalService = Depends(get_approval_service)
):
    """[DEPRECATED] Use /api/resources/approve instead."""
    logger.info(f"=== APPROVAL REQUEST RECEIVED (deprecated endpoint) ===")
    logger.info(f"Resource: {request.resource_name} (ID: {request.resource_id})")
    
    try:
        # Parse expiration_date string to datetime if provided
        expiration_datetime = None
        if request.expiration_date:
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
            return {
                "status": "success",
                "message": f"Resource {request.resource_name} approved successfully",
                "resource_id": request.resource_id,
                "workspace_id": request.workspace_id
            }
        else:
            raise ApprovalError("Failed to approve resource")
    except Exception as e:
        logger.error(f"Error approving resource: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/apps/revoke", deprecated=True, include_in_schema=False)
async def revoke_app_deprecated(
    request: RevokeRequest,
    service: ApprovalService = Depends(get_approval_service)
):
    """[DEPRECATED] Use /api/resources/revoke instead."""
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
    except Exception as e:
        logger.error(f"Error revoking approval: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/apps/refresh", deprecated=True, include_in_schema=False)
async def refresh_apps_deprecated(
    workspace_id: Optional[str] = Query(None),
    service: ApprovalService = Depends(get_approval_service)
):
    """[DEPRECATED] Use /api/resources/refresh instead."""
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
# SYSTEM ENDPOINTS
# ============================================================================
# Databricks Apps expects these endpoints


@app.get("/metrics")
async def metrics():
    """Metrics endpoint for Databricks Apps health checks."""
    # Return empty prometheus metrics format
    # In production, you could add actual metrics here
    return ""


# ============================================================================
# STATIC FILE SERVING (Frontend)
# ============================================================================
# These routes MUST be registered LAST so API routes match first
# Static file routes are registered at module level for proper route priority

static_dir = Path(__file__).parent.parent.parent / "frontend" / "dist"

if static_dir.exists() and (static_dir / "index.html").exists():
    logger.info(f"📁 Registering static file routes for: {static_dir}")
    
    # Mount static assets (JS, CSS, images, etc.)
    try:
        app.mount("/assets", StaticFiles(directory=str(static_dir / "assets")), name="assets")
        logger.info("✅ Mounted /assets directory")
    except Exception as e:
        logger.warning(f"⚠️  Could not mount /assets: {e}")
    
    # Serve index.html for root path
    @app.get("/", response_class=FileResponse)
    async def serve_frontend_root():
        """Serve the frontend SPA root."""
        return FileResponse(static_dir / "index.html")
    
    # Catch-all for client-side routing (e.g., /dashboard, /settings)
    # This MUST be the last route defined
    @app.get("/{full_path:path}", response_class=FileResponse)
    async def serve_frontend_spa(full_path: str):
        """Serve the frontend SPA for all non-API routes."""
        # Check if it's a static file request that wasn't caught by /assets mount
        file_path = static_dir / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        
        # Otherwise, serve index.html for client-side routing
        return FileResponse(static_dir / "index.html")
    
    logger.info("✅ Static file routes registered")
else:
    logger.warning(f"⚠️  Frontend not found at {static_dir}, serving API only")
    
    @app.get("/")
    async def api_root():
        """Root endpoint when frontend is not available."""
        return {
            "service": "Workspace Guardian API",
            "status": "running",
            "version": settings.app_version,
            "api_docs": "/docs"
        }
