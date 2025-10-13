"""Health check and root endpoints."""
import logging
from datetime import datetime

from fastapi import APIRouter

from ...config import settings
from ...dependencies import get_databricks_client

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Workspace Guardian",
        "status": "running",
        "version": settings.app_version
    }


@router.get("/api/health")
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

