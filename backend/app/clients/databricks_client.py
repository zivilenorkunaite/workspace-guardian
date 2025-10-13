"""Client for interacting with Databricks API."""
import os
import logging
from typing import List, Dict, Any, Optional
from databricks.sdk import WorkspaceClient

from ..config import settings

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
            # Local development - explicit credentials from settings (loaded from .env)
            host = settings.databricks_host
            token = settings.databricks_token
            
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
        # API: https://docs.databricks.com/api/workspace/apps/list
        # Note: SDK's get_apps() uses wrong endpoint, so we call REST API directly
        try:
            logger.debug("Fetching Databricks Apps via REST API /api/2.0/apps...")
            response = self.client.api_client.do('GET', '/api/2.0/apps')
            apps_list = response.get('apps', [])
            logger.info(f"Found {len(apps_list)} Databricks Apps")
            
            for app in apps_list:
                # Parse app data from REST response
                description = app.get('description', '')
                
                # Extract state from compute_status (actual field in API response)
                state = "UNKNOWN"
                if 'compute_status' in app:
                    compute_status = app['compute_status']
                    if isinstance(compute_status, dict) and 'state' in compute_status:
                        state = compute_status['state']
                    elif isinstance(compute_status, str):
                        state = compute_status
                
                # Fallback: try app_status (documented field, may vary by API version)
                if state == "UNKNOWN" and 'app_status' in app:
                    app_status = app['app_status']
                    if isinstance(app_status, dict) and 'state' in app_status:
                        state = app_status['state']
                    elif isinstance(app_status, str):
                        state = app_status
                
                logger.info(f"App '{app.get('name')}' state: {state}")
                
                resources.append({
                    "name": app.get('name', ''),
                    "resource_id": app.get('name', ''),  # Apps use name as ID
                    "state": state,
                    "creator": app.get('creator', 'unknown'),
                    "created_at": str(app.get('create_time')) if app.get('create_time') else None,
                    "description": description,
                    "workspace_id": ws_id,
                    "workspace_name": ws_name,
                    "type": "app"
                })
        except Exception as e:
            logger.error(f"Error listing Databricks Apps: {e}", exc_info=True)
        
        # 2. Model Serving Endpoints
        # API: https://docs.databricks.com/api/workspace/servingendpoints/list
        try:
            logger.debug("Fetching Model Serving Endpoints via serving_endpoints.list()...")
            endpoints_list = list(self.client.serving_endpoints.list())
            logger.info(f"Found {len(endpoints_list)} Model Serving Endpoints")
            
            for endpoint in endpoints_list:
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
        except Exception as e:
            logger.error(f"Error listing Model Serving Endpoints: {e}", exc_info=True)
        
        # 3. Vector Search Endpoints
        # API: https://docs.databricks.com/api/workspace/vectorsearchendpoints/listendpoints
        try:
            logger.debug("Fetching Vector Search Endpoints via REST API /api/2.0/vector-search/endpoints...")
            response = self.client.api_client.do('GET', '/api/2.0/vector-search/endpoints')
            endpoints_list = response.get('endpoints', [])
            logger.info(f"Found {len(endpoints_list)} Vector Search Endpoints")
            
            for endpoint in endpoints_list:
                # Extract endpoint type as description
                description = ""
                endpoint_type = endpoint.get('endpoint_type')
                if endpoint_type:
                    description = f"Type: {endpoint_type}"
                
                # Extract state from endpoint_status
                state = "UNKNOWN"
                endpoint_status = endpoint.get('endpoint_status', {})
                if endpoint_status and 'state' in endpoint_status:
                    state = endpoint_status['state']
                
                # Log state detection
                if state == "UNKNOWN":
                    logger.warning(f"Vector Search Endpoint '{endpoint.get('name')}' state could not be determined. Status: {endpoint_status}")
                
                resources.append({
                    "name": endpoint.get('name', ''),
                    "resource_id": endpoint.get('name', ''),
                    "state": state,
                    "creator": endpoint.get('creator', 'unknown'),
                    "created_at": str(endpoint.get('creation_timestamp')) if endpoint.get('creation_timestamp') else None,
                    "description": description,
                    "workspace_id": ws_id,
                    "workspace_name": ws_name,
                    "type": "vector_search"
                })
        except Exception as e:
            logger.error(f"Error listing Vector Search Endpoints: {e}", exc_info=True)
        
        # 4. Database Instances (Lakehouse Postgres)
        # API: https://docs.databricks.com/api/workspace/database/listdatabaseinstances
        try:
            logger.debug("Fetching Database Instances via REST API /api/2.0/database/instances...")
            response = self.client.api_client.do('GET', '/api/2.0/database/instances')
            database_instances = response.get('database_instances', [])
            logger.info(f"Found {len(database_instances)} Database Instances")
            
            for db_instance in database_instances:
                # Try to extract useful description from database instance details
                description = ""
                if db_instance.get('comment'):
                    description = db_instance['comment']
                elif db_instance.get('description'):
                    description = db_instance['description']
                elif db_instance.get('read_write_dns'):
                    description = f"Host: {db_instance['read_write_dns']}"
                
                # Extract state from database instance
                state = db_instance.get('state', db_instance.get('status', 'RUNNING'))
                
                # Log state detection
                logger.info(f"Database Instance '{db_instance.get('name')}' state: {state}")
                
                resources.append({
                    "name": db_instance.get('name', db_instance.get('uid', '')),
                    "resource_id": db_instance.get('uid', db_instance.get('name', '')),
                    "state": state,
                    "creator": db_instance.get('creator', 'unknown'),
                    "created_at": str(db_instance.get('created_at')) if db_instance.get('created_at') else None,
                    "description": description,
                    "workspace_id": ws_id,
                    "workspace_name": ws_name,
                    "type": "postgres"
                })
        except Exception as e:
            logger.error(f"Error listing Database Instances: {e}", exc_info=True)
        
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
            response = self.client.api_client.do('GET', f'/api/2.0/apps/{resource_name}')
            if response:
                app = response
                description = app.get('description', '')
                state = "UNKNOWN"
                if 'status' in app and 'state' in app['status']:
                    state = app['status']['state']
                
                return {
                    "name": app.get('name', resource_name),
                    "resource_id": app.get('name', resource_name),
                    "state": state,
                    "creator": app.get('creator', 'unknown'),
                    "created_at": str(app.get('create_time')) if app.get('create_time') else None,
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
                "created_at": str(endpoint.creation_timestamp) if endpoint.creation_timestamp else None,
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

