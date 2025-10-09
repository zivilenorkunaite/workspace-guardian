"""Unit tests for ApprovalService."""
import pytest
from datetime import datetime, timezone
from unittest.mock import Mock

from app.services.approval_service import ApprovalService
from app.exceptions import ValidationError


def test_list_resources_with_approvals(mock_databricks_client, mock_approval_repository):
    """Test listing resources with approval status."""
    service = ApprovalService(mock_databricks_client, mock_approval_repository)
    
    resources = service.list_resources_with_approvals()
    
    assert len(resources) > 0
    assert resources[0].name == "test-app"
    assert resources[0].is_approved is False  # No approvals in mock


def test_approve_resource_validation_error_no_name(mock_databricks_client, mock_approval_repository):
    """Test that approve_resource raises ValidationError for missing name."""
    service = ApprovalService(mock_databricks_client, mock_approval_repository)
    
    with pytest.raises(ValidationError, match="Resource name and ID are required"):
        service.approve_resource(
            resource_name="",
            resource_id="test-id",
            workspace_id="ws-123",
            workspace_name="test-ws",
            resource_creator="creator@example.com",
            approved_by="approver@example.com",
            justification="Valid justification here"
        )


def test_approve_resource_validation_error_short_justification(mock_databricks_client, mock_approval_repository):
    """Test that approve_resource raises ValidationError for short justification."""
    service = ApprovalService(mock_databricks_client, mock_approval_repository)
    
    with pytest.raises(ValidationError, match="Justification must be at least 10 characters"):
        service.approve_resource(
            resource_name="test-app",
            resource_id="test-id",
            workspace_id="ws-123",
            workspace_name="test-ws",
            resource_creator="creator@example.com",
            approved_by="approver@example.com",
            justification="short"
        )


def test_approve_resource_success(mock_databricks_client, mock_approval_repository):
    """Test successful resource approval."""
    service = ApprovalService(mock_databricks_client, mock_approval_repository)
    
    result = service.approve_resource(
        resource_name="test-app",
        resource_id="test-id",
        workspace_id="ws-123",
        workspace_name="test-ws",
        resource_creator="creator@example.com",
        approved_by="approver@example.com",
        justification="This is a valid justification with enough characters"
    )
    
    assert result is True
    mock_approval_repository.approve_resource.assert_called_once()


def test_revoke_approval_validation_error(mock_databricks_client, mock_approval_repository):
    """Test that revoke_approval raises ValidationError for short reason."""
    service = ApprovalService(mock_databricks_client, mock_approval_repository)
    
    with pytest.raises(ValidationError, match="Revocation reason must be at least 10 characters"):
        service.revoke_approval(
            resource_id="test-id",
            workspace_id="ws-123",
            revoked_by="revoker@example.com",
            revoked_reason="short"
        )


def test_revoke_approval_success(mock_databricks_client, mock_approval_repository):
    """Test successful revocation."""
    service = ApprovalService(mock_databricks_client, mock_approval_repository)
    
    result = service.revoke_approval(
        resource_id="test-id",
        workspace_id="ws-123",
        revoked_by="revoker@example.com",
        revoked_reason="This is a valid revocation reason"
    )
    
    assert result is True
    mock_approval_repository.revoke_approval.assert_called_once()

