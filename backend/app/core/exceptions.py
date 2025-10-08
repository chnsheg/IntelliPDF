"""
Custom exception hierarchy for IntelliPDF application.

This module defines all custom exceptions used throughout the application,
following a hierarchical structure for better error handling and logging.
"""

from typing import Any, Optional


class IntelliPDFException(Exception):
    """Base exception for all IntelliPDF custom exceptions."""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[dict[str, Any]] = None
    ) -> None:
        """
        Initialize base exception.

        Args:
            message: Human-readable error message
            error_code: Machine-readable error code
            details: Additional error context
        """
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to dictionary for API responses."""
        return {
            "error": self.error_code,
            "message": self.message,
            "details": self.details
        }


# ==================== Configuration Exceptions ====================

class ConfigurationError(IntelliPDFException):
    """Raised when application configuration is invalid."""
    pass


class EnvironmentError(ConfigurationError):
    """Raised when required environment variables are missing."""
    pass


# ==================== Processing Exceptions ====================

class ProcessingError(IntelliPDFException):
    """Raised when document processing fails."""
    pass


# ==================== File Processing Exceptions ====================

class FileProcessingError(IntelliPDFException):
    """Base exception for file processing errors."""
    pass


class FileNotFoundError(FileProcessingError):
    """Raised when a file cannot be found."""
    pass


class FileValidationError(FileProcessingError):
    """Raised when file validation fails."""
    pass


class FileSizeExceededError(FileValidationError):
    """Raised when uploaded file exceeds size limit."""
    pass


class UnsupportedFileTypeError(FileValidationError):
    """Raised when file type is not supported."""
    pass


# ==================== PDF Processing Exceptions ====================

class PDFProcessingError(IntelliPDFException):
    """Base exception for PDF processing errors."""
    pass


class PDFParseError(PDFProcessingError):
    """Raised when PDF parsing fails."""
    pass


class PDFExtractionError(PDFProcessingError):
    """Raised when content extraction from PDF fails."""
    pass


class PDFCorruptedError(PDFProcessingError):
    """Raised when PDF file is corrupted or invalid."""
    pass


class PDFPasswordProtectedError(PDFProcessingError):
    """Raised when PDF is password protected."""
    pass


class PDFPageLimitExceededError(PDFProcessingError):
    """Raised when PDF exceeds maximum page limit."""
    pass


# ==================== AI Service Exceptions ====================

class AIServiceError(IntelliPDFException):
    """Base exception for AI service errors."""
    pass


class OpenAIAPIError(AIServiceError):
    """Raised when OpenAI API call fails."""
    pass


class EmbeddingGenerationError(AIServiceError):
    """Raised when embedding generation fails."""
    pass


class LLMResponseError(AIServiceError):
    """Raised when LLM response is invalid or empty."""
    pass


class TokenLimitExceededError(AIServiceError):
    """Raised when content exceeds token limit."""
    pass


# ==================== Vector Database Exceptions ====================

class VectorDBError(IntelliPDFException):
    """Base exception for vector database errors."""
    pass


class ChromaDBConnectionError(VectorDBError):
    """Raised when connection to ChromaDB fails."""
    pass


class VectorSearchError(VectorDBError):
    """Raised when vector similarity search fails."""
    pass


class CollectionNotFoundError(VectorDBError):
    """Raised when vector collection doesn't exist."""
    pass


# ==================== Database Exceptions ====================

class DatabaseError(IntelliPDFException):
    """Base exception for database errors."""
    pass


class EntityNotFoundError(DatabaseError):
    """Raised when database entity is not found."""

    def __init__(self, entity_type: str, entity_id: Any) -> None:
        """
        Initialize entity not found error.

        Args:
            entity_type: Type of entity (e.g., "Document", "Chunk")
            entity_id: ID of the entity
        """
        message = f"{entity_type} with id {entity_id} not found"
        super().__init__(message, details={
            "entity_type": entity_type, "entity_id": entity_id})


class EntityAlreadyExistsError(DatabaseError):
    """Raised when attempting to create duplicate entity."""
    pass


class DatabaseConnectionError(DatabaseError):
    """Raised when database connection fails."""
    pass


class TransactionError(DatabaseError):
    """Raised when database transaction fails."""
    pass


# ==================== Authentication & Authorization Exceptions ====================

class AuthenticationError(IntelliPDFException):
    """Base exception for authentication errors."""
    pass


class InvalidCredentialsError(AuthenticationError):
    """Raised when authentication credentials are invalid."""
    pass


class TokenExpiredError(AuthenticationError):
    """Raised when authentication token has expired."""
    pass


class TokenInvalidError(AuthenticationError):
    """Raised when authentication token is invalid."""
    pass


class AuthorizationError(IntelliPDFException):
    """Raised when user lacks permission for operation."""
    pass


# ==================== Validation Exceptions ====================

class ValidationError(IntelliPDFException):
    """Base exception for validation errors."""
    pass


class InvalidInputError(ValidationError):
    """Raised when input validation fails."""
    pass


class SchemaValidationError(ValidationError):
    """Raised when data doesn't match expected schema."""
    pass


# ==================== Business Logic Exceptions ====================

class BusinessLogicError(IntelliPDFException):
    """Base exception for business logic errors."""
    pass


class ChunkingError(BusinessLogicError):
    """Raised when semantic chunking fails."""
    pass


class KnowledgeGraphError(BusinessLogicError):
    """Raised when knowledge graph operations fail."""
    pass


class BookmarkError(BusinessLogicError):
    """Raised when bookmark operations fail."""
    pass


class BookmarkNotFoundError(BookmarkError):
    """Raised when bookmark is not found."""
    pass


class UnauthorizedError(BookmarkError):
    """Raised when user is not authorized for bookmark operation."""
    pass


# ==================== External Service Exceptions ====================

class ExternalServiceError(IntelliPDFException):
    """Base exception for external service errors."""
    pass


class ServiceUnavailableError(ExternalServiceError):
    """Raised when external service is unavailable."""
    pass


class ServiceTimeoutError(ExternalServiceError):
    """Raised when external service request times out."""
    pass


class RateLimitExceededError(ExternalServiceError):
    """Raised when rate limit is exceeded."""
    pass
