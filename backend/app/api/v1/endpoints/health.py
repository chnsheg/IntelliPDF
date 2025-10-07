"""
Health check endpoint.

Provides system health status and version information.
"""

from fastapi import APIRouter
from pydantic import BaseModel

from ....core.config import get_settings

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    version: str
    environment: str


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Health check endpoint.

    Returns:
        HealthResponse: System health status
    """
    settings = get_settings()

    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        environment=settings.environment
    )
