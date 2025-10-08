"""
Domain model for text annotations.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from enum import Enum


class AnnotationType(str, Enum):
    """Annotation type enumeration."""
    HIGHLIGHT = "highlight"
    UNDERLINE = "underline"
    STRIKETHROUGH = "strikethrough"
    TAG = "tag"


class Position(BaseModel):
    """Position information for annotations."""
    x: float = Field(..., description="X coordinate")
    y: float = Field(..., description="Y coordinate")
    width: float = Field(..., description="Width")
    height: float = Field(..., description="Height")


class Annotation(BaseModel):
    """Domain model for text annotation."""

    id: str = Field(..., description="Annotation unique identifier")
    user_id: str = Field(..., description="Owner user ID")
    document_id: str = Field(..., description="Associated document ID")
    chunk_id: Optional[str] = Field(None, description="Associated chunk ID")

    annotation_type: AnnotationType = Field(...,
                                            description="Type of annotation")
    content: str = Field(..., description="Annotated text content")
    page_number: int = Field(..., description="Page number", ge=1)

    position: Position = Field(..., description="Position information")
    color: str = Field(
        "#FFFF00", description="Color in hex format", pattern=r"^#[0-9A-Fa-f]{6}$")

    tag_id: Optional[str] = Field(
        None, description="Associated tag ID for tag-type annotations")
    notes: Optional[str] = Field(None, description="User notes")

    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "user_id": "user123",
                "document_id": "doc456",
                "annotation_type": "highlight",
                "content": "Important text to remember",
                "page_number": 5,
                "position": {"x": 100.0, "y": 200.0, "width": 150.0, "height": 20.0},
                "color": "#FFFF00",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        }
