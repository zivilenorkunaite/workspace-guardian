"""FastAPI main application for Workspace Guardian."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .dependencies import initialize_migrations
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
