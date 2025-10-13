"""FastAPI dependency injection providers."""
import logging
from functools import lru_cache
from typing import Optional

from .config import settings
from .clients import DatabricksClient
from .database import DatabaseConnection, SQLExecutor, MigrationManager
from .repositories import ApprovalRepository
from .services import ApprovalService
from .exceptions import ClientInitializationError

logger = logging.getLogger(__name__)


# Singletons
_databricks_client: Optional[DatabricksClient] = None
_sql_executor: Optional[SQLExecutor] = None
_approval_repository: Optional[ApprovalRepository] = None
_migrations_initialized: bool = False


@lru_cache()
def get_databricks_client() -> DatabricksClient:
    """
    Get Databricks client (singleton).
    
    Returns:
        DatabricksClient instance
        
    Raises:
        ClientInitializationError: If client cannot be initialized
    """
    global _databricks_client
    
    if _databricks_client is None:
        logger.info("Initializing Databricks client...")
        _databricks_client = DatabricksClient()
        logger.info("✅ Databricks client initialized")
    
    return _databricks_client


def get_sql_executor() -> SQLExecutor:
    """
    Get SQL executor (singleton).
    
    Returns:
        SQLExecutor instance
    """
    global _sql_executor
    
    if _sql_executor is None:
        logger.info("Initializing SQL executor...")
        workspace_client = DatabaseConnection.get_client()
        _sql_executor = SQLExecutor(workspace_client)
        logger.info("✅ SQL executor initialized")
    
    return _sql_executor


def get_approval_repository() -> ApprovalRepository:
    """
    Get approval repository (singleton).
    
    Returns:
        ApprovalRepository instance
    """
    global _approval_repository
    
    if _approval_repository is None:
        logger.info("Initializing approval repository...")
        executor = get_sql_executor()
        _approval_repository = ApprovalRepository(executor)
        logger.info("✅ Approval repository initialized")
    
    return _approval_repository


def get_approval_service() -> ApprovalService:
    """
    Get approval service (singleton).
    
    Returns:
        ApprovalService instance
    """
    logger.info("Creating approval service...")
    client = get_databricks_client()
    repository = get_approval_repository()
    return ApprovalService(client, repository)


def initialize_migrations() -> None:
    """
    Initialize database migrations (run once on startup).
    
    Raises:
        Exception: If migrations fail
    """
    global _migrations_initialized
    
    if _migrations_initialized:
        logger.info("⏭️  Migrations already attempted this session, skipping...")
        return
    
    try:
        logger.info("=" * 70)
        logger.info("🔄 Initializing database migrations...")
        logger.info("=" * 70)
        
        executor = get_sql_executor()
        migration_manager = MigrationManager(executor)
        migration_manager.run_migrations()
        
        logger.info("=" * 70)
        logger.info("✅ Database migrations completed successfully")
        logger.info("=" * 70)
        
    except Exception as e:
        logger.error(f"❌ Database migration failed: {e}")
        raise
    finally:
        # Always mark as initialized (even on failure) to prevent retry spam
        # This is safe because migrations are idempotent and will be checked again on next app start
        _migrations_initialized = True
        logger.debug("Migration initialization attempt recorded")


def reset_singletons() -> None:
    """Reset all singletons (useful for testing)."""
    global _databricks_client, _sql_executor, _approval_repository, _migrations_initialized
    
    _databricks_client = None
    _sql_executor = None
    _approval_repository = None
    _migrations_initialized = False
    
    DatabaseConnection.reset()
    get_databricks_client.cache_clear()
    
    logger.info("✅ All singletons reset")

