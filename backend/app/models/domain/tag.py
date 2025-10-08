"""
Domain model for tags.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class Tag(BaseModel):
    """Domain model for organizing annotations and bookmarks."""

    id: str = Field(..., description="Tag unique identifier")
    user_id: str = Field(..., description="Owner user ID")
    name: str = Field(..., description="Tag name", min_length=1, max_length=50)
    color: str = Field(
        "#3B82F6", description="Tag color in hex format", pattern=r"^#[0-9A-Fa-f]{6}$")
    description: Optional[str] = Field(None, description="Tag description")

    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "tag123",
                "user_id": "user456",
                "name": "重要概念",
                "color": "#3B82F6",
                "description": "标记文档中的重要概念",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        }
