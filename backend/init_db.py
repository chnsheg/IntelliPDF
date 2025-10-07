"""
Database initialization script.

Creates all tables if they don't exist.
"""

from app.models.db.base import Base
from app.infrastructure.database.session import get_engine
from app.core.logging import get_logger
from app.core.config import get_settings
import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))


logger = get_logger(__name__)
settings = get_settings()


async def init_database():
    """
    Initialize database by creating all tables.
    """
    logger.info("Initializing database...")

    try:
        # Get engine
        engine = get_engine(settings)

        # Create all tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        logger.info("✅ Database initialized successfully!")
        logger.info(f"Database URL: {settings.database_url}")

        # List created tables
        async with engine.begin() as conn:
            tables = await conn.run_sync(
                lambda sync_conn: sync_conn.dialect.get_table_names(sync_conn)
            )
            logger.info(f"Created tables: {', '.join(tables)}")

    except Exception as e:
        logger.error(f"❌ Failed to initialize database: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(init_database())
