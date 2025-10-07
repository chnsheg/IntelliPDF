"""
Dependency injection container for IntelliPDF application.

This module provides centralized dependency management using FastAPI's
dependency injection system for services, repositories, and external clients.
"""

from typing import AsyncGenerator, Generator

from sqlalchemy.ext.asyncio import AsyncSession

from ..infrastructure.database.session import get_db_session
from .config import Settings, get_settings


async def get_settings_dependency() -> Settings:
    """
    Dependency for injecting application settings.

    Returns:
        Settings: Application configuration
    """
    return get_settings()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for injecting database session.

    Yields:
        AsyncSession: SQLAlchemy async database session
    """
    async for session in get_db_session():
        yield session


# Service dependencies will be added as services are implemented
# Example structure:
#
# async def get_pdf_service(
#     db: AsyncSession = Depends(get_db),
#     settings: Settings = Depends(get_settings_dependency)
# ) -> PDFProcessingService:
#     """Get PDF processing service instance."""
#     return PDFProcessingService(db=db, settings=settings)
