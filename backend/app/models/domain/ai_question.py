"""
Domain model for AI questions with context.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class AIQuestion(BaseModel):
    """Domain model for context-based AI questions."""

    id: str = Field(..., description="Question unique identifier")
    user_id: str = Field(..., description="User ID")
    document_id: str = Field(..., description="Associated document ID")
    chunk_id: Optional[str] = Field(None, description="Context chunk ID")

    selected_text: str = Field(...,
                               description="Selected text being questioned")
    context_text: Optional[str] = Field(
        None, description="Surrounding context from chunk")
    user_question: str = Field(...,
                               description="User's question about the selected text")
    ai_answer: str = Field(..., description="AI-generated answer")

    page_number: int = Field(..., description="Page number", ge=1)
    position_x: float = Field(..., description="X coordinate")
    position_y: float = Field(..., description="Y coordinate")

    model_used: str = Field("gemini-1.5-flash", description="AI model used")
    response_metadata: Optional[dict] = Field(
        None, description="Additional response metadata")

    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "q123",
                "user_id": "user456",
                "document_id": "doc789",
                "selected_text": "Linux系统调用",
                "context_text": "...关于Linux系统调用的详细说明...",
                "user_question": "这个参数mode有什么作用?",
                "ai_answer": "mode参数用于指定文件的权限设置...",
                "page_number": 160,
                "position_x": 100.0,
                "position_y": 200.0,
                "model_used": "gemini-1.5-flash",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        }
