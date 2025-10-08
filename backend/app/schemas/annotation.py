"""
Pydantic schemas for annotations.

Defines request and response models for annotation endpoints.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class AnnotationPosition(BaseModel):
    x: float = Field(..., description="X coordinate")
    y: float = Field(..., description="Y coordinate")
    width: float = Field(..., gt=0, description="Selection width")
    height: float = Field(..., gt=0, description="Selection height")


class AnnotationBase(BaseModel):
    annotation_type: str = Field(..., description="Type of annotation")
    page_number: Optional[int] = Field(None, ge=0, description="Page number")
    position: Optional[AnnotationPosition] = Field(
        None, description="Position")
    color: Optional[str] = Field(None, description="Color")
    content: Optional[str] = Field(
        None, description="User note or tagged text")
    tags: Optional[List[str]] = Field(default=[], description="Tags")


class AnnotationCreate(AnnotationBase):
    document_id: str = Field(..., description="Document ID")
    user_id: str = Field(..., description="Owner user ID")


class AnnotationUpdate(BaseModel):
    color: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[List[str]] = None


class AnnotationResponse(BaseModel):
    id: str
    document_id: str
    user_id: str
    annotation_type: str
    page_number: Optional[int]
    position: Optional[Dict[str, Any]]
    color: Optional[str]
    content: Optional[str]
    tags: List[str]
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AnnotationListResponse(BaseModel):
    annotations: List[AnnotationResponse]
    total: int
