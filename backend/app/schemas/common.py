"""
Common Pydantic schemas used across the API.

This module contains common schemas like pagination, status responses, etc.
"""

from typing import Optional
from pydantic import BaseModel, Field


class PaginationParams(BaseModel):
    """
    Pagination parameters for list endpoints.
    """
    skip: int = Field(0, ge=0, description="Number of records to skip")
    limit: int = Field(100, ge=1, le=1000,
                       description="Maximum number of records to return")


class StatusResponse(BaseModel):
    """
    Generic status response.
    """
    success: bool = Field(..., description="Operation success status")
    message: Optional[str] = Field(None, description="Status message")


class ErrorResponse(BaseModel):
    """
    Error response schema.
    """
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    detail: Optional[str] = Field(
        None, description="Detailed error information")

    class Config:
        json_schema_extra = {
            "example": {
                "error": "ValidationError",
                "message": "Invalid input data",
                "detail": "Field 'filename' is required"
            }
        }
