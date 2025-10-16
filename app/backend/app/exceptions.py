"""Custom exceptions for Workspace Guardian."""
from typing import Optional, Any, Dict


class WorkspaceGuardianException(Exception):
    """Base exception for all Workspace Guardian errors."""
    
    def __init__(
        self, 
        message: str, 
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        super().__init__(self.message)


class ClientInitializationError(WorkspaceGuardianException):
    """Raised when client initialization fails."""
    pass


class ResourceNotFoundError(WorkspaceGuardianException):
    """Raised when a requested resource is not found."""
    pass


class ApprovalError(WorkspaceGuardianException):
    """Raised when an approval operation fails."""
    pass


class RevocationError(WorkspaceGuardianException):
    """Raised when a revocation operation fails."""
    pass


class DatabaseError(WorkspaceGuardianException):
    """Raised when a database operation fails."""
    pass


class MigrationError(WorkspaceGuardianException):
    """Raised when a migration operation fails."""
    pass


class ValidationError(WorkspaceGuardianException):
    """Raised when validation fails."""
    pass


class AuthenticationError(WorkspaceGuardianException):
    """Raised when authentication fails."""
    pass


class AuthorizationError(WorkspaceGuardianException):
    """Raised when authorization fails."""
    pass

