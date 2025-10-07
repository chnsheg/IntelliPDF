"""
Chunk-related Pydantic schemas.

This module contains schemas for chunk data.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

from ..models.domain.chunk import ChunkType


class BoundingBox(BaseModel):
    """Bounding box for chunk position in PDF."""
    page: int = Field(..., description="Page number (1-based)")
    x0: float = Field(..., description="Left coordinate")
    y0: float = Field(..., description="Top coordinate")
    x1: float = Field(..., description="Right coordinate")
    y1: float = Field(..., description="Bottom coordinate")


class ChunkBase(BaseModel):
    """
    Base chunk schema with common fields.
    """
    content: str = Field(..., min_length=1, description="Chunk content text")
    chunk_index: int = Field(..., ge=0, description="Chunk index in document")
    chunk_type: ChunkType = Field(..., description="Type of chunk")
    bounding_boxes: Optional[List[BoundingBox]] = Field(None, description="Bounding boxes for chunk position")


class ChunkCreate(ChunkBase):
    """
    Schema for creating a new chunk.
    """
    document_id: UUID = Field(..., description="Parent document ID")
    start_page: int = Field(..., ge=1, description="Starting page number")
    end_page: int = Field(..., ge=1, description="Ending page number")
    token_count: int = Field(..., ge=0, description="Number of tokens")
    chunk_metadata: Optional[Dict[str, Any]] = Field(
        None, description="Chunk metadata", alias="metadata")


class ChunkInDB(ChunkBase):
    """
    Chunk schema as stored in database.
    """
    id: UUID
    document_id: UUID
    start_page: int
    end_page: int
    token_count: int
    vector_id: Optional[str] = None
    chunk_metadata: Optional[Dict[str, Any]] = Field(None, alias="metadata")
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChunkResponse(ChunkInDB):
    """
    Chunk response schema for API endpoints.
    """

    class Config:
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174001",
                "document_id": "123e4567-e89b-12d3-a456-426614174000",
                "content": "这是第一个分块的内容...",
                "chunk_index": 0,
                "chunk_type": "section",
                "start_page": 1,
                "end_page": 3,
                "token_count": 512,
                "vector_id": "vec_123abc",
                "bounding_boxes": [
                    {"page": 1, "x0": 72, "y0": 100, "x1": 540, "y1": 300},
                    {"page": 2, "x0": 72, "y0": 100, "x1": 540, "y1": 200}
                ],
                "metadata": {
                    "chapter": "第一章",
                    "section": "1.1 简介"
                },
                "created_at": "2025-10-07T10:01:00Z",
                "updated_at": "2025-10-07T10:01:00Z"
            }
        }


class ChunkListResponse(BaseModel):
    """
    Response schema for chunk list endpoint.
    """
    document_id: UUID = Field(..., description="Document ID")
    total: int = Field(..., description="Total number of chunks")
    chunks: List[ChunkResponse] = Field(..., description="List of chunks")

    class Config:
        json_schema_extra = {
            "example": {
                "document_id": "123e4567-e89b-12d3-a456-426614174000",
                "total": 134,
                "chunks": [
                    # ... chunk examples
                ]
            }
        }
