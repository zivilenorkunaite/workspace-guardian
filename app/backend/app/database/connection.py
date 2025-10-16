"""Database connection management for Databricks."""
import logging
from typing import Optional
from databricks.sdk import WorkspaceClient

from ..config import settings
from ..exceptions import ClientInitializationError

logger = logging.getLogger(__name__)


class DatabaseConnection:
    """Manages Databricks WorkspaceClient connection."""
    
    _instance: Optional[WorkspaceClient] = None
    
    @classmethod
    def get_client(cls) -> WorkspaceClient:
        """
        Get or create WorkspaceClient instance (singleton pattern).
        
        Returns:
            WorkspaceClient instance
            
        Raises:
            ClientInitializationError: If client cannot be initialized
        """
        if cls._instance is None:
            cls._instance = cls._create_client()
        return cls._instance
    
    @classmethod
    def _create_client(cls) -> WorkspaceClient:
        """
        Create a new WorkspaceClient instance.
        
        Returns:
            WorkspaceClient instance
            
        Raises:
            ClientInitializationError: If client cannot be initialized
        """
        try:
            if settings.is_databricks_app:
                # Databricks App - automatic authentication
                client = WorkspaceClient()
                logger.info("✅ Using Databricks App authentication")
            else:
                # Local development - explicit credentials
                if not settings.databricks_host or not settings.databricks_token:
                    raise ClientInitializationError(
                        "Local development requires DATABRICKS_HOST and DATABRICKS_TOKEN. "
                        "For Databricks App deployment, these are not needed."
                    )
                
                client = WorkspaceClient(
                    host=settings.databricks_host,
                    token=settings.databricks_token
                )
                logger.info(f"✅ Using local development credentials for {settings.databricks_host}")
            
            logger.info("✅ Databricks client initialized successfully")
            return client
            
        except ClientInitializationError:
            raise
        except Exception as e:
            logger.error(f"❌ Failed to initialize Databricks client: {e}")
            raise ClientInitializationError(
                f"Failed to initialize Databricks client: {e}",
                details={"error": str(e)}
            )
    
    @classmethod
    def reset(cls):
        """Reset the singleton instance (useful for testing)."""
        cls._instance = None

