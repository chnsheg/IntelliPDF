"""
Document-related Pydantic schemas.

This module contains schemas for document creation, updates, and responses.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

from ..models.domain.document import DocumentStatus


class DocumentBase(BaseModel):
    """
    Base document schema with common fields.
    """
    filename: str = Field(..., min_length=1, max_length=255,
                          description="Original filename")
    doc_metadata: Optional[Dict[str, Any]] = Field(
        None, description="Document metadata", alias="metadata")


class DocumentCreate(DocumentBase):
    """
    Schema for creating a new document.
    """
    file_path: str = Field(..., description="File storage path")
    file_size: int = Field(..., gt=0, description="File size in bytes")
    content_hash: str = Field(..., min_length=64,
                              max_length=64, description="SHA-256 hash")


class DocumentUpdate(BaseModel):
    """
    Schema for updating document information.
    """
    filename: Optional[str] = Field(None, min_length=1, max_length=255)
    doc_metadata: Optional[Dict[str, Any]] = Field(None, alias="metadata")
    status: Optional[DocumentStatus] = None


class DocumentInDB(DocumentBase):
    """
    Document schema as stored in database.
    """
    id: UUID
    file_path: str
    file_size: int
    content_hash: str
    status: DocumentStatus
    processing_started_at: Optional[datetime] = None
    processing_completed_at: Optional[datetime] = None
    processing_error: Optional[str] = None
    chunk_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentResponse(DocumentInDB):
    """
    Document response schema for API endpoints.
    """

    class Config:
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "filename": "论文.pdf",
                "file_path": "/uploads/2025/10/论文.pdf",
                "file_size": 1024000,
                "content_hash": "abc123...",
                "status": "completed",
                "processing_started_at": "2025-10-07T10:00:00Z",
                "processing_completed_at": "2025-10-07T10:01:30Z",
                "processing_error": None,
                "metadata": {
                    "title": "研究论文",
                    "author": "张三",
                    "pages": 122
                },
                "chunk_count": 134,
                "created_at": "2025-10-07T10:00:00Z",
                "updated_at": "2025-10-07T10:01:30Z"
            }
        }


class DocumentListResponse(BaseModel):
    """
    Response schema for document list endpoint.
    """
    total: int = Field(..., description="Total number of documents")
    skip: int = Field(..., description="Number of records skipped")
    limit: int = Field(..., description="Maximum records returned")
    documents: List[DocumentResponse] = Field(...,
                                              description="List of documents")


class DocumentStatistics(BaseModel):
    """
    Document statistics schema.
    """
    total: int = Field(..., description="Total number of documents")
    by_status: Dict[str, int] = Field(..., description="Count by status")
    total_size: int = Field(..., description="Total size in bytes")

    class Config:
        json_schema_extra = {
            "example": {
                "total": 10,
                "by_status": {
                    "pending": 1,
                    "processing": 2,
                    "completed": 6,
                    "failed": 1
                },
                "total_size": 102400000
            }
        }
