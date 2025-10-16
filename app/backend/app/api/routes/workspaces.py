"""Workspace management endpoints."""
import logging
from typing import List

from fastapi import APIRouter, HTTPException

from ...models import Workspace
from ...dependencies import get_databricks_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/workspaces", tags=["workspaces"])


@router.get("", response_model=List[Workspace])
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

