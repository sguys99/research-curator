"""Custom exceptions for vector database operations."""


class VectorDBError(Exception):
    """Base exception for vector DB errors."""


class VectorDBConnectionError(VectorDBError):
    """Raised when unable to connect to the vector DB."""


class VectorDBOperationError(VectorDBError):
    """Raised when a vector DB operation fails."""
