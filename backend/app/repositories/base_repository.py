"""
Base repository with common CRUD operations.

This module provides a generic base repository class that can be extended
by specific repositories to provide type-safe database operations.
"""

from typing import Generic, TypeVar, Type, Optional, List, Any, Dict
from uuid import UUID

from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase

from ..core.logging import get_logger

logger = get_logger(__name__)

# Type variables for generic repository
ModelType = TypeVar("ModelType", bound=DeclarativeBase)


class BaseRepository(Generic[ModelType]):
    """
    Base repository with common CRUD operations.

    This class provides generic database operations that can be used
    by all repositories. It uses SQLAlchemy 2.0 async API.

    Type Parameters:
        ModelType: SQLAlchemy model class
    """

    def __init__(self, model: Type[ModelType], session: AsyncSession):
        """
        Initialize repository.

        Args:
            model: SQLAlchemy model class
            session: Async database session
        """
        self.model = model
        self.session = session

    async def create(self, obj: ModelType) -> ModelType:
        """
        Create a new record.

        Args:
            obj: Model instance to create

        Returns:
            Created model instance with database-generated values
        """
        self.session.add(obj)
        await self.session.flush()
        await self.session.refresh(obj)
        logger.debug(
            f"Created {self.model.__name__} with id: {getattr(obj, 'id', None)}")
        return obj

    async def get_by_id(self, id: UUID) -> Optional[ModelType]:
        """
        Get a record by ID.

        Args:
            id: Record UUID

        Returns:
            Model instance or None if not found
        """
        # CRITICAL FIX: Convert UUID to string for SQLite compatibility
        # Database stores UUIDs as String(36), but API passes UUID objects
        id_str = str(id) if isinstance(id, UUID) else id

        result = await self.session.execute(
            select(self.model).where(self.model.id == id_str)
        )
        obj = result.scalar_one_or_none()
        if obj:
            logger.debug(f"Found {self.model.__name__} with id: {id}")
        else:
            logger.debug(f"{self.model.__name__} not found with id: {id}")
        return obj

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        order_by: Optional[Any] = None
    ) -> List[ModelType]:
        """
        Get all records with pagination.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            order_by: Optional ordering clause

        Returns:
            List of model instances
        """
        query = select(self.model)

        if order_by is not None:
            query = query.order_by(order_by)

        query = query.offset(skip).limit(limit)

        result = await self.session.execute(query)
        objects = result.scalars().all()
        logger.debug(f"Retrieved {len(objects)} {self.model.__name__} records")
        return list(objects)

    async def count(self) -> int:
        """
        Count total records.

        Returns:
            Total number of records
        """
        result = await self.session.execute(
            select(func.count()).select_from(self.model)
        )
        count = result.scalar_one()
        logger.debug(f"Total {self.model.__name__} count: {count}")
        return count

    async def update(self, id: UUID, values: Dict[str, Any]) -> Optional[ModelType]:
        """
        Update a record by ID.

        Args:
            id: Record UUID
            values: Dictionary of field names and new values

        Returns:
            Updated model instance or None if not found
        """
        # First check if record exists
        obj = await self.get_by_id(id)
        if not obj:
            return None

        # CRITICAL FIX: Convert UUID to string for SQLite compatibility
        id_str = str(id) if isinstance(id, UUID) else id

        # Update the record
        await self.session.execute(
            update(self.model)
            .where(self.model.id == id_str)
            .values(**values)
        )
        await self.session.flush()

        # Refresh to get updated values
        await self.session.refresh(obj)
        logger.info(f"Updated {self.model.__name__} with id: {id}")
        return obj

    async def delete(self, id: UUID) -> bool:
        """
        Delete a record by ID.

        Args:
            id: Record UUID

        Returns:
            True if deleted, False if not found
        """
        # CRITICAL FIX: Convert UUID to string for SQLite compatibility
        id_str = str(id) if isinstance(id, UUID) else id

        result = await self.session.execute(
            delete(self.model).where(self.model.id == id_str)
        )
        deleted = result.rowcount > 0

        if deleted:
            logger.info(f"Deleted {self.model.__name__} with id: {id}")
        else:
            logger.debug(f"{self.model.__name__} not found with id: {id}")

        return deleted

    async def exists(self, id: UUID) -> bool:
        """
        Check if a record exists.

        Args:
            id: Record UUID

        Returns:
            True if exists, False otherwise
        """
        # CRITICAL FIX: Convert UUID to string for SQLite compatibility
        id_str = str(id) if isinstance(id, UUID) else id

        result = await self.session.execute(
            select(func.count()).select_from(
                self.model).where(self.model.id == id_str)
        )
        count = result.scalar_one()
        return count > 0

    async def commit(self) -> None:
        """
        Commit the current transaction.
        """
        await self.session.commit()
        logger.debug(f"Transaction committed for {self.model.__name__}")

    async def rollback(self) -> None:
        """
        Rollback the current transaction.
        """
        await self.session.rollback()
        logger.warning(f"Transaction rolled back for {self.model.__name__}")
