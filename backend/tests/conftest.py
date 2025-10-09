"""Pytest configuration and fixtures."""
import pytest
from unittest.mock import Mock, MagicMock


@pytest.fixture
def mock_databricks_client():
    """Mock Databricks client."""
    client = Mock()
    client.workspace_id = "test-workspace-123"
    client.workspace_name = "test-workspace"
    client.list_apps.return_value = [
        {
            "name": "test-app",
            "resource_id": "test-app-id",
            "state": "RUNNING",
            "creator": "test@example.com",
            "created_at": "2024-01-01T00:00:00Z",
            "description": "Test app",
            "workspace_id": "test-workspace-123",
            "workspace_name": "test-workspace",
            "type": "app"
        }
    ]
    return client


@pytest.fixture
def mock_sql_executor():
    """Mock SQL executor."""
    executor = Mock()
    executor.execute.return_value = []
    return executor


@pytest.fixture
def mock_approval_repository():
    """Mock approval repository."""
    repo = Mock()
    repo.get_approved_resources.return_value = []
    repo.approve_resource.return_value = True
    repo.revoke_approval.return_value = True
    return repo


@pytest.fixture
def sample_resource_data():
    """Sample resource data for testing."""
    return {
        "name": "test-app",
        "resource_id": "test-app-id",
        "state": "RUNNING",
        "creator": "test@example.com",
        "created_at": "2024-01-01T00:00:00Z",
        "description": "Test app",
        "workspace_id": "test-workspace-123",
        "workspace_name": "test-workspace",
        "type": "app"
    }


@pytest.fixture
def sample_approval_data():
    """Sample approval data for testing."""
    return {
        "resource_name": "test-app",
        "resource_id": "test-app-id",
        "workspace_id": "test-workspace-123",
        "workspace_name": "test-workspace",
        "resource_creator": "test@example.com",
        "approved_by": "approver@example.com",
        "justification": "This is a test approval with sufficient justification"
    }

