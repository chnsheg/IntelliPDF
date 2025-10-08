"""
Bookmark-related Pydantic schemas.

Request/response models for bookmark endpoints.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


# ==================== Position Schema ====================

class BookmarkPosition(BaseModel):
    """Bookmark position (bounding box)."""

    x: float = Field(..., description="X coordinate")
    y: float = Field(..., description="Y coordinate")
    width: float = Field(..., gt=0, description="Selection width")
    height: float = Field(..., gt=0, description="Selection height")


# ==================== Bookmark Schemas ====================

class BookmarkBase(BaseModel):
    """Base bookmark schema with common fields."""

    selected_text: str = Field(..., min_length=1,
                               description="Selected text content")
    page_number: int = Field(..., ge=0, description="Page number")
    position: BookmarkPosition = Field(..., description="Position information")
    title: Optional[str] = Field(
        None, max_length=200, description="Bookmark title")
    user_notes: Optional[str] = Field(None, description="User notes")
    tags: Optional[List[str]] = Field(default=[], description="User tags")
    color: str = Field(default="#FCD34D", description="Highlight color")


class BookmarkCreate(BookmarkBase):
    """Schema for creating a bookmark."""

    document_id: str = Field(..., description="Document ID")
    chunk_id: Optional[str] = Field(None, description="Associated chunk ID")
    conversation_history: Optional[List[Dict[str, str]]] = Field(
        None,
        description="Conversation history for AI summary generation"
    )


class BookmarkUpdate(BaseModel):
    """Schema for updating a bookmark."""

    title: Optional[str] = Field(None, max_length=200)
    user_notes: Optional[str] = None
    tags: Optional[List[str]] = None
    color: Optional[str] = None


class BookmarkResponse(BaseModel):
    """Schema for bookmark response."""

    id: str = Field(..., description="Bookmark ID")
    user_id: str = Field(..., description="Owner user ID")
    document_id: str = Field(..., description="Document ID")
    chunk_id: Optional[str] = Field(None, description="Associated chunk ID")
    selected_text: str = Field(..., description="Selected text content")
    page_number: int = Field(..., description="Page number")

    # Position as separate fields (matching database model)
    position_x: float = Field(..., description="X coordinate")
    position_y: float = Field(..., description="Y coordinate")
    position_width: float = Field(..., description="Selection width")
    position_height: float = Field(..., description="Selection height")

    ai_summary: str = Field(..., description="AI-generated summary")
    title: Optional[str] = Field(None, description="Bookmark title")
    user_notes: Optional[str] = Field(None, description="User notes")
    tags: Optional[List[str]] = Field(default=[], description="User tags")
    color: str = Field(..., description="Highlight color")
    conversation_context: Optional[Dict[str, Any]] = Field(
        None, description="Associated conversation")
    created_at: datetime = Field(..., description="Creation time")
    updated_at: datetime = Field(..., description="Last update time")

    class Config:
        from_attributes = True


# ==================== List Response ====================

class BookmarkListResponse(BaseModel):
    """Schema for bookmark list response."""

    bookmarks: List[BookmarkResponse] = Field(...,
                                              description="List of bookmarks")
    total: int = Field(..., description="Total count")


# ==================== Search Request ====================

class BookmarkSearchRequest(BaseModel):
    """Schema for bookmark search request."""

    query: str = Field(..., min_length=1, description="Search query")
    document_id: Optional[str] = Field(
        None, description="Optional document filter")


# ==================== AI Generate Request ====================

class BookmarkGenerateRequest(BaseModel):
    """Schema for AI bookmark generation request."""

    document_id: str = Field(..., description="Document ID")
    selected_text: str = Field(..., min_length=1, description="Selected text")
    page_number: int = Field(..., ge=0, description="Page number")
    position: BookmarkPosition = Field(..., description="Position")
    conversation_history: Optional[List[Dict[str, str]]] = Field(
        default=[],
        description="Conversation history"
    )
    chunk_id: Optional[str] = None
    color: str = Field(default="#FCD34D")


# ==================== Statistics ====================

class BookmarkStatistics(BaseModel):
    """Bookmark statistics."""

    total_bookmarks: int = Field(..., description="Total bookmark count")
    documents_with_bookmarks: int = Field(...,
                                          description="Documents with bookmarks")
    bookmarks_this_week: int = Field(...,
                                     description="Bookmarks created this week")
    most_bookmarked_document: Optional[Dict[str, Any]] = Field(
        None, description="Most bookmarked document")
