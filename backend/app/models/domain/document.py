"""
Document domain models.

This module defines the core domain models for PDF documents,
representing the business logic layer independent of database implementation.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, validator


class DocumentStatus(str, Enum):
    """Document processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class DocumentMetadata(BaseModel):
    """
    Metadata extracted from PDF document.

    Contains bibliographic and technical information about the document.
    """

    title: Optional[str] = Field(
        None,
        description="Document title from PDF metadata"
    )
    author: Optional[str] = Field(
        None,
        description="Document author"
    )
    subject: Optional[str] = Field(
        None,
        description="Document subject"
    )
    keywords: Optional[list[str]] = Field(
        default_factory=list,
        description="Document keywords"
    )
    creator: Optional[str] = Field(
        None,
        description="PDF creator application"
    )
    producer: Optional[str] = Field(
        None,
        description="PDF producer"
    )
    creation_date: Optional[datetime] = Field(
        None,
        description="PDF creation date"
    )
    modification_date: Optional[datetime] = Field(
        None,
        description="PDF last modification date"
    )
    page_count: int = Field(
        ...,
        ge=1,
        description="Total number of pages"
    )
    language: Optional[str] = Field(
        None,
        description="Document language code (ISO 639-1)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Introduction to Machine Learning",
                "author": "John Doe",
                "subject": "Artificial Intelligence",
                "keywords": ["machine learning", "AI", "neural networks"],
                "creator": "LaTeX",
                "producer": "pdfTeX-1.40.21",
                "creation_date": "2024-01-01T00:00:00",
                "modification_date": "2024-01-15T12:00:00",
                "page_count": 150,
                "language": "en"
            }
        }


class Document(BaseModel):
    """
    Core document domain model.

    Represents a PDF document in the system with its metadata,
    processing status, and relationships.
    """

    id: UUID = Field(
        default_factory=uuid4,
        description="Document unique identifier (UUIDv4)"
    )
    filename: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Original filename"
    )
    file_path: str = Field(
        ...,
        description="File storage path"
    )
    file_size: int = Field(
        ...,
        gt=0,
        le=500 * 1024 * 1024,  # 500MB max
        description="File size in bytes"
    )
    content_hash: str = Field(
        ...,
        min_length=64,
        max_length=64,
        description="SHA-256 hash of file content"
    )
    status: DocumentStatus = Field(
        default=DocumentStatus.PENDING,
        description="Document processing status"
    )
    metadata: Optional[DocumentMetadata] = Field(
        None,
        description="Extracted document metadata"
    )
    processing_started_at: Optional[datetime] = Field(
        None,
        description="When processing started"
    )
    processing_completed_at: Optional[datetime] = Field(
        None,
        description="When processing completed"
    )
    processing_error: Optional[str] = Field(
        None,
        description="Error message if processing failed"
    )
    chunk_count: int = Field(
        default=0,
        ge=0,
        description="Number of semantic chunks extracted"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Record creation timestamp (UTC)"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Record last update timestamp (UTC)"
    )

    @validator("filename")
    def validate_filename(cls, v: str) -> str:
        """Validate filename format."""
        if not v.lower().endswith('.pdf'):
            raise ValueError("Filename must end with .pdf")
        return v

    @validator("updated_at", always=True)
    def set_updated_at(cls, v: datetime, values: dict) -> datetime:
        """Auto-update timestamp."""
        return datetime.utcnow()

    class Config:
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "filename": "machine_learning_guide.pdf",
                "file_path": "/data/uploads/2024/01/machine_learning_guide.pdf",
                "file_size": 15728640,
                "content_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                "status": "completed",
                "metadata": {
                    "title": "Machine Learning Guide",
                    "author": "Jane Smith",
                    "page_count": 200
                },
                "chunk_count": 456,
                "created_at": "2024-01-01T10:00:00",
                "updated_at": "2024-01-01T10:30:00"
            }
        }


class DocumentUploadRequest(BaseModel):
    """Request model for document upload."""

    filename: str = Field(
        ...,
        description="Original filename"
    )

    @validator("filename")
    def validate_filename(cls, v: str) -> str:
        """Validate filename."""
        if not v.lower().endswith('.pdf'):
            raise ValueError("Only PDF files are supported")
        return v


class DocumentResponse(BaseModel):
    """Response model for document operations."""

    id: UUID
    filename: str
    file_size: int
    status: DocumentStatus
    metadata: Optional[DocumentMetadata]
    chunk_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
