"""
Pydantic schemas for PDF annotations.
Handles validation and serialization for annotation API endpoints.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


# Base schemas for annotation data structures (matching frontend types)
class TextAnchorSchema(BaseModel):
    """Text anchor for text-based annotations"""
    selectedText: str
    prefix: str
    suffix: str
    pageNumber: int
    startOffset: int
    endOffset: int
    textHash: str


class QuadPointSchema(BaseModel):
    """PDF QuadPoint (4-corner quadrilateral)"""
    x1: float
    y1: float
    x2: float
    y2: float
    x3: float
    y3: float
    x4: float
    y4: float


class PDFCoordinatesSchema(BaseModel):
    """PDF native coordinates"""
    pageNumber: int
    quadPoints: List[QuadPointSchema]
    rotation: int = 0
    pageWidth: float
    pageHeight: float


class AnnotationStyleSchema(BaseModel):
    """Annotation style properties"""
    type: Optional[str] = None  # highlight, underline, strikethrough, squiggly
    color: str = "#FAEB96"
    opacity: float = Field(default=0.45, ge=0.0, le=1.0)
    fillColor: Optional[str] = None
    strokeColor: Optional[str] = None
    strokeWidth: Optional[float] = None
    lineStyle: Optional[str] = None


# Annotation creation schemas
class AnnotationCreateBase(BaseModel):
    """Base schema for creating annotations"""
    document_id: str
    user_id: str
    annotation_type: str  # text-markup, shape, ink, textbox, note, stamp, signature
    page_number: int = Field(ge=1)
    # Complete annotation data (textAnchor, pdfCoordinates, style)
    data: Dict[str, Any]
    content: Optional[str] = None
    color: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    user_name: Optional[str] = None


class AnnotationCreate(AnnotationCreateBase):
    """Schema for creating new annotation"""
    pass


class AnnotationUpdate(BaseModel):
    """Schema for updating annotation"""
    data: Optional[Dict[str, Any]] = None
    content: Optional[str] = None
    color: Optional[str] = None
    tags: Optional[List[str]] = None

    class Config:
        extra = "forbid"


# Annotation response schemas
class AnnotationResponse(BaseModel):
    """Schema for annotation in API responses"""
    id: str
    document_id: str
    user_id: str
    annotation_type: str
    page_number: int
    data: Dict[str, Any]
    content: Optional[str] = None
    color: Optional[str] = None
    tags: List[str]
    user_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AnnotationListResponse(BaseModel):
    """Schema for paginated annotation list"""
    annotations: List[AnnotationResponse]
    total: int
    page: int = 1
    page_size: int = 50
    has_more: bool = False


# Annotation reply schemas
class AnnotationReplyCreate(BaseModel):
    """Schema for creating annotation reply"""
    annotation_id: str
    user_id: str
    content: str
    parent_reply_id: Optional[str] = None
    user_name: Optional[str] = None


class AnnotationReplyResponse(BaseModel):
    """Schema for reply in API responses"""
    id: str
    annotation_id: str
    user_id: str
    parent_reply_id: Optional[str] = None
    content: str
    user_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Batch operation schemas
class AnnotationBatchDelete(BaseModel):
    """Schema for deleting multiple annotations"""
    annotation_ids: List[str]


# Filter schemas
class AnnotationFilter(BaseModel):
    """Schema for filtering annotations"""
    document_id: Optional[str] = None
    page_number: Optional[int] = None
    annotation_type: Optional[str] = None
    user_id: Optional[str] = None
    tags: Optional[List[str]] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
