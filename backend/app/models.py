"""Pydantic models for API request/response validation."""
from typing import Optional, List
from pydantic import BaseModel


class Workspace(BaseModel):
    """Databricks workspace information."""
    id: str
    name: str
    url: str


class DatabricksResource(BaseModel):
    """Databricks resource (app, endpoint, connection, etc.) information."""
    name: str
    resource_id: str
    state: str
    creator: str
    created_at: Optional[str] = None
    workspace_id: str
    workspace_name: str
    type: str
    is_approved: bool = False
    approval_date: Optional[str] = None
    approved_by: Optional[str] = None
    expiration_date: Optional[str] = None
    justification: Optional[str] = None
    description: Optional[str] = None


class ResourcesResponse(BaseModel):
    """Response containing list of resources."""
    resources: List[DatabricksResource]
    workspace_id: str
    workspace_name: str


class ApprovalRequest(BaseModel):
    """Request to approve a resource."""
    resource_name: str
    resource_id: str
    workspace_id: str
    workspace_name: str
    resource_creator: str
    approved_by: str
    expiration_date: Optional[str] = None
    justification: str


class RevokeRequest(BaseModel):
    """Request to revoke a resource approval."""
    resource_name: str
    resource_id: str
    workspace_id: str
    revoked_by: str
    revoked_reason: str


class ApprovedResource(BaseModel):
    """An approved resource with full details."""
    resource_name: str
    resource_id: str
    workspace_id: str
    workspace_name: str
    resource_creator: str
    approved_by: str
    approval_date: str
    expiration_date: Optional[str] = None
    justification: str
    is_approved: bool
    revoked_date: Optional[str] = None
    revoked_by: Optional[str] = None
    revoked_reason: Optional[str] = None


class ApprovalResponse(BaseModel):
    """Response after approval action."""
    success: bool
    message: str
    resource: Optional[ApprovedResource] = None


class RefreshResponse(BaseModel):
    """Response after refresh action."""
    success: bool
    message: str
    resources_synced: int

