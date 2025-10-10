"""Client for interacting with Databricks API."""
import os
import logging
from typing import List, Dict, Any, Optional
from databricks.sdk import WorkspaceClient

logger = logging.getLogger(__name__)


class DatabricksClient:
    """Client for interacting with Databricks workspaces and resources."""
    
    def __init__(self):
        """Initialize Databricks client with automatic or explicit authentication."""
        is_databricks_app = os.getenv("DATABRICKS_RUNTIME_VERSION") is not None
        
        if is_databricks_app:
            # Databricks App - automatic authentication
            self.client = WorkspaceClient()
            logger.info("Using Databricks App authentication")
        else:
            # Local development - explicit credentials
            host = os.getenv("DATABRICKS_HOST")
            token = os.getenv("DATABRICKS_TOKEN")
            
            if not host or not token:
                raise Exception("Local development requires DATABRICKS_HOST and DATABRICKS_TOKEN. For Databricks App deployment, these are not needed.")
            
            self.client = WorkspaceClient(host=host, token=token)
            logger.info(f"Using explicit credentials for host: {host}")
        
        self.workspace_id = self._get_current_workspace_id()
        self.workspace_name = self._get_workspace_name()
        logger.info(f"Connected to workspace: {self.workspace_name} (ID: {self.workspace_id})")
    
    def get_accessible_workspaces(self) -> List[Dict[str, str]]:
        """
        Get list of accessible workspaces.
        
        For now, returns current workspace only.
        Multi-workspace support can be added via Account API.
        
        Returns:
            List of workspace dictionaries with id, name, url
        """
        return [{
            "id": self.workspace_id,
            "name": self.workspace_name,
            "url": self.client.config.host if hasattr(self.client.config, 'host') else ""
        }]
    
    def list_apps(self, workspace_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all Databricks resources (Apps, Serving Endpoints, Vector Search, Connections).
        Kept for backward compatibility - calls list_resources().
        
        Args:
            workspace_id: Optional workspace ID (currently unused, always returns current workspace)
        
        Returns:
            List of resource dictionaries with unified schema.
        """
        return self.list_resources()
    
    def list_resources(self) -> List[Dict[str, Any]]:
        """
        List all Databricks resources (Apps, Serving Endpoints, Vector Search, Connections).
        
        Returns:
            List of resource dictionaries with unified schema.
        """
        resources = []
        ws_id = self.workspace_id
        ws_name = self.workspace_name
        
        # 1. Databricks Apps
        try:
            apps = self.client.apps.list()
            for app in apps:
                description = app.description if hasattr(app, 'description') and app.description else ""
                resources.append({
                    "name": app.name,
                    "resource_id": app.name,  # Apps use name as ID
                    "state": app.status.state.value if app.status and app.status.state else "UNKNOWN",
                    "creator": app.creator or "unknown",
                    "created_at": str(app.create_time) if app.create_time else None,
                    "description": description,
                    "workspace_id": ws_id,
                    "workspace_name": ws_name,
                    "type": "app"
                })
            logger.info(f"Found {len(list(apps))} Databricks Apps")
        except Exception as e:
            logger.error(f"Error listing apps: {e}")
        
        # 2. Model Serving Endpoints
        try:
            endpoints = self.client.serving_endpoints.list()
            for endpoint in endpoints:
                # Get description from API
                description = ""
                if hasattr(endpoint, 'description') and endpoint.description:
                    description = endpoint.description
                elif hasattr(endpoint, 'config') and endpoint.config:
                    # Fallback: extract model names if no description
                    if hasattr(endpoint.config, 'served_models') and endpoint.config.served_models:
                        model_names = [m.model_name for m in endpoint.config.served_models if hasattr(m, 'model_name')]
                        if model_names:
                            description = f"Serving models: {', '.join(model_names)}"
                
                resources.append({
                    "name": endpoint.name,
                    "resource_id": endpoint.id or endpoint.name,
                    "state": endpoint.state.ready.value if endpoint.state and endpoint.state.ready else "UNKNOWN",
                    "creator": endpoint.creator or "unknown",
                    "created_at": str(endpoint.creation_timestamp) if endpoint.creation_timestamp else None,
                    "description": description,
                    "workspace_id": ws_id,
                    "workspace_name": ws_name,
                    "type": "serving_endpoint"
                })
            logger.info(f"Found {len(list(endpoints))} Serving Endpoints")
        except Exception as e:
            logger.error(f"Error listing serving endpoints: {e}")
        
        # 3. Vector Search Endpoints
        try:
            vector_endpoints = self.client.vector_search_endpoints.list_endpoints()
            for endpoint in vector_endpoints.endpoints or []:
                # Extract endpoint type as description
                description = ""
                if hasattr(endpoint, 'endpoint_type') and endpoint.endpoint_type:
                    description = f"Type: {endpoint.endpoint_type}"
                
                resources.append({
                    "name": endpoint.name,
                    "resource_id": endpoint.name,
                    "state": endpoint.endpoint_status.state.value if endpoint.endpoint_status and endpoint.endpoint_status.state else "UNKNOWN",
                    "creator": endpoint.creator or "unknown",
                    "created_at": str(endpoint.creation_timestamp) if endpoint.creation_timestamp else None,
                    "description": description,
                    "workspace_id": ws_id,
                    "workspace_name": ws_name,
                    "type": "vector_search"
                })
            logger.info(f"Found {len(vector_endpoints.endpoints or [])} Vector Search Endpoints")
        except Exception as e:
            logger.error(f"Error listing vector search endpoints: {e}")
        
        # 4. Lakehouse Postgres Connections
        try:
            connections = self.client.connections.list()
            for conn in connections:
                # Try to extract useful description from connection details
                description = ""
                if hasattr(conn, 'options') and conn.options:
                    # Try to get comment or description from options
                    if 'comment' in conn.options:
                        description = conn.options['comment']
                    elif 'description' in conn.options:
                        description = conn.options['description']
                    elif 'host' in conn.options:
                        description = f"Host: {conn.options['host']}"
                
                resources.append({
                    "name": conn.name,
                    "resource_id": conn.name,
                    "state": "RUNNING" if conn.read_only is False else "UNKNOWN",
                    "creator": conn.owner or "unknown",
                    "created_at": str(conn.created_at) if conn.created_at else None,
                    "description": description,
                    "workspace_id": ws_id,
                    "workspace_name": ws_name,
                    "type": "postgres"
                })
            logger.info(f"Found {len(list(connections))} Lakehouse Postgres Connections")
        except Exception as e:
            logger.error(f"Error listing connections: {e}")
        
        logger.info(f"Total resources found: {len(resources)}")
        return resources
    
    def get_resource_details(self, resource_name: str) -> Optional[Dict[str, Any]]:
        """
        Get details for a specific resource.
        
        Args:
            resource_name: Name of the resource
            
        Returns:
            Resource dictionary or None if not found
        """
        ws_id = self.workspace_id
        ws_name = self.workspace_name
        
        # Try as Databricks App
        try:
            app = self.client.apps.get(name=resource_name)
            description = app.description if hasattr(app, 'description') and app.description else ""
            if app:
                return {
                    "name": app.name,
                    "resource_id": app.name,
                    "state": app.status.state.value if app.status and app.status.state else "UNKNOWN",
                    "creator": app.creator or "unknown",
                    "created_at": str(app.create_time) if app.create_time else None,
                    "description": description,
                    "workspace_id": ws_id,
                    "workspace_name": ws_name,
                    "type": "app"
                }
        except Exception:
            pass
        
        # Try as serving endpoint
        try:
            endpoint = self.client.serving_endpoints.get(name=resource_name)
            # Get description from API
            description = ""
            if hasattr(endpoint, 'description') and endpoint.description:
                description = endpoint.description
            elif hasattr(endpoint, 'config') and endpoint.config:
                # Fallback: extract model names if no description
                if hasattr(endpoint.config, 'served_models') and endpoint.config.served_models:
                    model_names = [m.model_name for m in endpoint.config.served_models if hasattr(m, 'model_name')]
                    if model_names:
                        description = f"Serving models: {', '.join(model_names)}"
            
            return {
                "name": endpoint.name,
                "resource_id": endpoint.id or endpoint.name,
                "state": endpoint.state.ready.value if endpoint.state and endpoint.state.ready else "UNKNOWN",
                "creator": endpoint.creator or "unknown",
                "created_at": str(endpoint.creation_timestamp) if endpoint.creation_timestamp else "",
                "description": description,
                "workspace_id": ws_id,
                "workspace_name": ws_name,
                "type": "serving_endpoint"
            }
        except Exception as e:
            logger.error(f"Resource not found: {resource_name}: {e}")
            return None
    
    def _get_current_workspace_id(self) -> str:
        """Get the current workspace ID."""
        try:
            workspace = self.client.workspace.get_status("/")
            # Extract workspace ID from the object_id or use a default
            return str(workspace.object_id) if workspace and workspace.object_id else "default"
        except Exception as e:
            logger.warning(f"Could not get workspace ID: {e}")
            return "default"
    
    def _get_workspace_name(self) -> str:
        """Get workspace display name from host."""
        try:
            # Try to get from config
            if hasattr(self.client.config, 'host') and self.client.config.host:
                host = self.client.config.host
                # Extract workspace name from URL (e.g., https://my-workspace.cloud.databricks.com)
                if '://' in host:
                    host = host.split('://')[1]
                workspace_name = host.split('.')[0]
                return workspace_name
        except Exception as e:
            logger.warning(f"Could not determine workspace name: {e}")
        
        return "default-workspace"

