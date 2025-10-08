"""
Pydantic schemas for tag endpoints.
"""

from typing import Optional, List
from pydantic import BaseModel, Field


# Request Schemas
class TagCreate(BaseModel):
    """Schema for creating a new tag."""
    name: str = Field(..., description="Tag name", min_length=1, max_length=50)
    color: str = Field(
        "#3B82F6", description="Tag color in hex format", pattern=r"^#[0-9A-Fa-f]{6}$")
    description: Optional[str] = Field(None, description="Tag description")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "重要概念",
                "color": "#3B82F6",
                "description": "标记文档中的重要概念"
            }
        }


class TagUpdate(BaseModel):
    """Schema for updating a tag."""
    name: Optional[str] = Field(
        None, description="Tag name", min_length=1, max_length=50)
    color: Optional[str] = Field(
        None, description="Tag color in hex format", pattern=r"^#[0-9A-Fa-f]{6}$")
    description: Optional[str] = Field(None, description="Tag description")

    class Config:
        json_schema_extra = {
            "example": {
                "color": "#FF5722",
                "description": "Updated description"
            }
        }


# Response Schemas
class TagResponse(BaseModel):
    """Schema for tag response."""
    id: str
    user_id: str
    name: str
    color: str
    description: Optional[str]
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class TagListResponse(BaseModel):
    """Schema for list of tags."""
    tags: List[TagResponse]
    total: int = Field(..., description="Total number of tags")

    class Config:
        json_schema_extra = {
            "example": {
                "tags": [],
                "total": 0
            }
        }
