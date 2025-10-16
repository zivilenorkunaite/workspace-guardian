"""Configuration management for Workspace Guardian."""
import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field

# Find workspace root (go up from backend/app/ to workspace root)
WORKSPACE_ROOT = Path(__file__).parent.parent.parent
ENV_FILE_PATH = WORKSPACE_ROOT / ".env"


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Databricks Configuration (Local Development Only)
    databricks_host: Optional[str] = Field(None, env="DATABRICKS_HOST")
    databricks_token: Optional[str] = Field(None, env="DATABRICKS_TOKEN")
    databricks_warehouse_id: Optional[str] = Field(None, env="DATABRICKS_WAREHOUSE_ID")
    
    # Unity Catalog Configuration
    app_catalog: str = Field("main", env="APP_CATALOG")
    app_schema: str = Field("workspace_guardian", env="APP_SCHEMA")
    
    # Application Configuration
    app_version: str = Field("1.0.0", env="APP_VERSION")
    log_level: str = Field("INFO", env="LOG_LEVEL")
    
    # Runtime Detection
    @property
    def is_databricks_app(self) -> bool:
        """Check if running as Databricks App."""
        return os.getenv("DATABRICKS_RUNTIME_VERSION") is not None
    
    @property
    def requires_explicit_auth(self) -> bool:
        """Check if explicit authentication is required."""
        return not self.is_databricks_app
    
    class Config:
        # Look for .env in workspace root (dynamically resolved)
        env_file = str(ENV_FILE_PATH)
        case_sensitive = False


# Global settings instance
settings = Settings()

