"""
Pydantic schemas for AI question endpoints.
"""

from typing import Optional, List
from pydantic import BaseModel, Field


# Request Schemas
class AIQuestionCreate(BaseModel):
    """Schema for creating an AI question with context."""
    document_id: str = Field(..., description="Document ID")
    chunk_id: Optional[str] = Field(None, description="Context chunk ID")
    selected_text: str = Field(..., description="Selected text", min_length=1)
    user_question: str = Field(...,
                               description="User's question", min_length=1)
    page_number: int = Field(..., description="Page number", ge=1)
    position_x: float = Field(..., description="X coordinate")
    position_y: float = Field(..., description="Y coordinate")

    class Config:
        json_schema_extra = {
            "example": {
                "document_id": "doc789",
                "selected_text": "Linux系统调用",
                "user_question": "这个参数mode有什么作用?",
                "page_number": 160,
                "position_x": 100.0,
                "position_y": 200.0
            }
        }


# Response Schemas
class AIQuestionResponse(BaseModel):
    """Schema for AI question response."""
    id: str
    user_id: str
    document_id: str
    chunk_id: Optional[str]
    selected_text: str
    context_text: Optional[str]
    user_question: str
    ai_answer: str
    page_number: int
    position_x: float
    position_y: float
    model_used: str
    response_metadata: Optional[dict]
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class AIQuestionListResponse(BaseModel):
    """Schema for list of AI questions."""
    questions: List[AIQuestionResponse]
    total: int = Field(..., description="Total number of questions")

    class Config:
        json_schema_extra = {
            "example": {
                "questions": [],
                "total": 0
            }
        }


# Query Schemas
class AIQuestionQuery(BaseModel):
    """Schema for querying AI questions."""
    document_id: Optional[str] = Field(
        None, description="Filter by document ID")
    page_number: Optional[int] = Field(
        None, description="Filter by page number")
    skip: int = Field(0, ge=0, description="Number of records to skip")
    limit: int = Field(100, ge=1, le=1000,
                       description="Maximum number of records")

    class Config:
        json_schema_extra = {
            "example": {
                "document_id": "doc789",
                "page_number": 160,
                "skip": 0,
                "limit": 100
            }
        }
