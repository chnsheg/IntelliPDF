"""
Database session management for IntelliPDF.

This module provides async database session management using SQLAlchemy 2.0
with connection pooling and proper lifecycle management.
"""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool, QueuePool

from ...core.config import Settings, get_settings
from ...core.logging import get_logger

logger = get_logger(__name__)

# Global engine instance
_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine(settings: Settings | None = None) -> AsyncEngine:
    """
    Get or create async database engine.

    Args:
        settings: Optional settings override

    Returns:
        AsyncEngine: SQLAlchemy async engine
    """
    global _engine

    if _engine is None:
        if settings is None:
            settings = get_settings()

        # Choose pool class based on environment and database type
        is_sqlite = "sqlite" in settings.database_url

        if is_sqlite:
            # SQLite doesn't support pool_size, max_overflow, or server_settings
            _engine = create_async_engine(
                settings.database_url,
                echo=settings.database_echo,
                poolclass=NullPool,
            )
        elif settings.is_production:
            _engine = create_async_engine(
                settings.database_url,
                echo=settings.database_echo,
                poolclass=QueuePool,
                pool_size=settings.database_pool_size,
                max_overflow=settings.database_max_overflow,
                pool_pre_ping=True,
                pool_recycle=3600,
                connect_args={
                    "server_settings": {
                        "application_name": "intellipdf",
                    }
                }
            )
        else:
            _engine = create_async_engine(
                settings.database_url,
                echo=settings.database_echo,
                poolclass=NullPool,
            )

        logger.info(
            f"Database engine created for {settings.environment} environment")

    return _engine


def get_session_factory(settings: Settings | None = None) -> async_sessionmaker[AsyncSession]:
    """
    Get or create async session factory.

    Args:
        settings: Optional settings override

    Returns:
        async_sessionmaker: Session factory
    """
    global _session_factory

    if _session_factory is None:
        engine = get_engine(settings)
        _session_factory = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
        logger.info("Session factory created")

    return _session_factory


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting database session.

    Provides proper session lifecycle management with automatic
    commit/rollback and cleanup.

    Yields:
        AsyncSession: Database session
    """
    session_factory = get_session_factory()

    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {str(e)}")
            raise
        finally:
            await session.close()


async def close_engine() -> None:
    """Close database engine and cleanup resources."""
    global _engine, _session_factory

    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _session_factory = None
        logger.info("Database engine closed")
