"""
Semantic chunk domain models.

This module defines models for semantic chunks extracted from documents,
representing meaningful units of content with their context and relationships.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, validator


class ChunkType(str, Enum):
    """Type of content chunk."""
    TEXT = "text"
    CODE = "code"
    IMAGE = "image"
    TABLE = "table"
    FORMULA = "formula"
    HEADING = "heading"
    LIST = "list"
    FOOTNOTE = "footnote"


class BBox(BaseModel):
    """
    Bounding box coordinates for content location in PDF.

    Uses PDF coordinate system (bottom-left origin).
    """

    page: int = Field(
        ...,
        ge=1,
        description="Page number (1-indexed)"
    )
    x0: float = Field(
        ...,
        ge=0.0,
        description="Left x coordinate"
    )
    y0: float = Field(
        ...,
        ge=0.0,
        description="Bottom y coordinate"
    )
    x1: float = Field(
        ...,
        ge=0.0,
        description="Right x coordinate"
    )
    y1: float = Field(
        ...,
        ge=0.0,
        description="Top y coordinate"
    )

    @validator("x1")
    def x1_greater_than_x0(cls, v: float, values: dict) -> float:
        """Ensure x1 > x0."""
        if "x0" in values and v <= values["x0"]:
            raise ValueError("x1 must be greater than x0")
        return v

    @validator("y1")
    def y1_greater_than_y0(cls, v: float, values: dict) -> float:
        """Ensure y1 > y0."""
        if "y0" in values and v <= values["y0"]:
            raise ValueError("y1 must be greater than y0")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "page": 1,
                "x0": 72.0,
                "y0": 400.0,
                "x1": 540.0,
                "y1": 700.0
            }
        }


class SemanticChunk(BaseModel):
    """
    Semantic chunk extracted from document.

    Represents a meaningful unit of content with semantic context,
    structural information, and vector embedding for similarity search.
    """

    chunk_id: UUID = Field(
        default_factory=uuid4,
        description="Chunk global unique identifier"
    )
    document_id: UUID = Field(
        ...,
        description="Parent document ID"
    )
    content: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="Chunk text content"
    )
    chunk_type: ChunkType = Field(
        ...,
        description="Type of content chunk"
    )
    semantic_topic: Optional[str] = Field(
        None,
        max_length=500,
        description="AI-extracted semantic topic or summary"
    )
    importance_score: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Importance score (0-1) for ranking"
    )
    vector_embedding: Optional[list[float]] = Field(
        None,
        description="Vector embedding for similarity search"
    )
    structural_path: list[str] = Field(
        default_factory=list,
        description="Document structure path (e.g., ['Chapter 1', 'Section 1.2'])"
    )
    bounding_box: Optional[BBox] = Field(
        None,
        description="Precise location in original document"
    )
    sequence_number: int = Field(
        ...,
        ge=0,
        description="Sequence order within document (0-indexed)"
    )
    char_count: int = Field(
        ...,
        ge=0,
        description="Character count"
    )
    word_count: int = Field(
        ...,
        ge=0,
        description="Word count"
    )
    language: Optional[str] = Field(
        None,
        description="Detected language code (ISO 639-1)"
    )
    metadata: dict = Field(
        default_factory=dict,
        description="Additional chunk-specific metadata"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Creation timestamp (UTC)"
    )

    @validator("vector_embedding")
    def validate_embedding_dimension(cls, v: Optional[list[float]]) -> Optional[list[float]]:
        """Validate embedding dimension."""
        if v is not None and len(v) not in [768, 1536, 3072]:
            raise ValueError("Embedding dimension must be 768, 1536, or 3072")
        return v

    @validator("word_count", always=True)
    def calculate_word_count(cls, v: int, values: dict) -> int:
        """Auto-calculate word count if not provided."""
        if v == 0 and "content" in values:
            return len(values["content"].split())
        return v

    @validator("char_count", always=True)
    def calculate_char_count(cls, v: int, values: dict) -> int:
        """Auto-calculate character count if not provided."""
        if v == 0 and "content" in values:
            return len(values["content"])
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "chunk_id": "123e4567-e89b-12d3-a456-426614174000",
                "document_id": "987fcdeb-51a2-43d7-9abc-123456789012",
                "content": "Machine learning is a subset of artificial intelligence...",
                "chunk_type": "text",
                "semantic_topic": "Introduction to Machine Learning",
                "importance_score": 0.85,
                "structural_path": ["Chapter 1", "Section 1.1"],
                "bounding_box": {
                    "page": 1,
                    "x0": 72.0,
                    "y0": 400.0,
                    "x1": 540.0,
                    "y1": 700.0
                },
                "sequence_number": 0,
                "char_count": 150,
                "word_count": 25,
                "language": "en"
            }
        }


class ChunkQueryRequest(BaseModel):
    """Request model for chunk queries."""

    query: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Search query text"
    )
    document_id: Optional[UUID] = Field(
        None,
        description="Filter by document ID"
    )
    chunk_types: Optional[list[ChunkType]] = Field(
        None,
        description="Filter by chunk types"
    )
    max_results: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Maximum number of results"
    )
    min_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Minimum similarity score threshold"
    )


class ChunkResponse(BaseModel):
    """Response model for chunk operations."""

    chunk_id: UUID
    document_id: UUID
    content: str
    chunk_type: ChunkType
    semantic_topic: Optional[str]
    importance_score: float
    structural_path: list[str]
    sequence_number: int
    similarity_score: Optional[float] = Field(
        None,
        description="Similarity score when returned from search"
    )

    class Config:
        from_attributes = True
