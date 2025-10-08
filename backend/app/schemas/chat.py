"""
Chat-related Pydantic schemas.

This module contains schemas for chat/RAG interactions.
"""

from typing import Optional, List, Literal
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class Message(BaseModel):
    """
    Chat message schema.
    """
    role: Literal["user", "assistant", "system"] = Field(
        ..., description="Message role (user/assistant/system)")
    content: str = Field(..., min_length=1, description="Message content")
    timestamp: Optional[datetime] = Field(
        None, description="Message timestamp")


class ChunkSource(BaseModel):
    """
    Source chunk schema.
    """
    chunk_id: str = Field(..., description="Chunk identifier")
    content: str = Field(..., description="Chunk content")
    page: Optional[int] = Field(None, description="Page number")
    similarity: Optional[float] = Field(None, description="Similarity score")
    # Frontend-friendly aliases (kept for compatibility)
    page_number: Optional[int] = Field(None, description="Page number (alias)")
    similarity_score: Optional[float] = Field(
        None, description="Similarity score (alias)")


class ChatRequest(BaseModel):
    """
    Request schema for chat endpoint.
    """
    question: str = Field(..., min_length=1, max_length=2000,
                          description="User question")
    conversation_history: Optional[List[Message]] = Field(
        default=None,
        description="Previous conversation messages for context"
    )
    top_k: int = Field(
        default=5, ge=1, le=20, description="Number of chunks to retrieve")
    temperature: float = Field(
        default=0.7, ge=0.0, le=2.0, description="LLM temperature")

    class Config:
        json_schema_extra = {
            "example": {
                "question": "Linux中如何查看系统信息?",
                "conversation_history": [
                    {
                        "role": "user",
                        "content": "Linux有哪些常用命令?",
                        "timestamp": "2025-10-07T10:00:00Z"
                    },
                    {
                        "role": "assistant",
                        "content": "Linux常用命令包括ls、cd、mkdir等...",
                        "timestamp": "2025-10-07T10:00:05Z"
                    }
                ],
                "top_k": 5,
                "temperature": 0.7
            }
        }


class ChatResponse(BaseModel):
    """
    Response schema for chat endpoint.
    """
    answer: str = Field(..., description="Generated answer")
    sources: List[ChunkSource] = Field(
        default_factory=list,
        description="Source chunks used for answer"
    )
    document_id: UUID = Field(..., description="Document ID")
    question: str = Field(..., description="Original question")
    processing_time: float = Field(...,
                                   description="Processing time in seconds")

    class Config:
        json_schema_extra = {
            "example": {
                "answer": "查看Linux系统信息可以使用以下命令:\n1. uname -a: 查看内核版本...",
                "sources": [
                    {
                        "chunk_id": "123e4567-e89b-12d3-a456-426614174001",
                        "content": "uname命令用于显示系统信息...",
                        "page": 42,
                        "similarity": 0.89
                    }
                ],
                "document_id": "123e4567-e89b-12d3-a456-426614174000",
                "question": "Linux中如何查看系统信息?",
                "processing_time": 2.34
            }
        }
