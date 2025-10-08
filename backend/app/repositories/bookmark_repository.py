"""
Bookmark repository for database operations.

This module provides data access methods for bookmark entities.
"""

from typing import Optional, List
from sqlalchemy import select, and_

from .base_repository import BaseRepository
from ..models.db import BookmarkModel
from ..core.logging import get_logger

logger = get_logger(__name__)


class BookmarkRepository(BaseRepository[BookmarkModel]):
    """Repository for bookmark database operations."""

    def __init__(self, session):
        """
        Initialize bookmark repository.

        Args:
            session: Async database session
        """
        super().__init__(BookmarkModel, session)

    async def get_by_user(
        self,
        user_id: str,
        limit: Optional[int] = None
    ) -> List[BookmarkModel]:
        """
        Get all bookmarks for a user.

        Args:
            user_id: User ID
            limit: Optional limit on number of results

        Returns:
            List of bookmark models
        """
        try:
            stmt = select(BookmarkModel).where(
                BookmarkModel.user_id == user_id
            ).order_by(BookmarkModel.created_at.desc())

            if limit:
                stmt = stmt.limit(limit)

            result = await self.session.execute(stmt)
            bookmarks = result.scalars().all()

            logger.info(
                f"Found {len(bookmarks)} bookmarks for user: {user_id}")
            return list(bookmarks)
        except Exception as e:
            logger.error(f"Error getting bookmarks by user: {e}")
            raise

    async def get_by_document(
        self,
        document_id: str,
        user_id: Optional[str] = None
    ) -> List[BookmarkModel]:
        """
        Get all bookmarks for a document.

        Args:
            document_id: Document ID
            user_id: Optional user ID filter

        Returns:
            List of bookmark models
        """
        try:
            stmt = select(BookmarkModel).where(
                BookmarkModel.document_id == document_id
            )

            if user_id:
                stmt = stmt.where(BookmarkModel.user_id == user_id)

            stmt = stmt.order_by(BookmarkModel.page_number,
                                 BookmarkModel.position_y)

            result = await self.session.execute(stmt)
            bookmarks = result.scalars().all()

            logger.info(
                f"Found {len(bookmarks)} bookmarks for document: {document_id}")
            return list(bookmarks)
        except Exception as e:
            logger.error(f"Error getting bookmarks by document: {e}")
            raise

    async def get_by_page(
        self,
        document_id: str,
        page_number: int,
        user_id: Optional[str] = None
    ) -> List[BookmarkModel]:
        """
        Get bookmarks for a specific page.

        Args:
            document_id: Document ID
            page_number: Page number
            user_id: Optional user ID filter

        Returns:
            List of bookmark models
        """
        try:
            conditions = [
                BookmarkModel.document_id == document_id,
                BookmarkModel.page_number == page_number
            ]

            if user_id:
                conditions.append(BookmarkModel.user_id == user_id)

            stmt = select(BookmarkModel).where(
                and_(*conditions)
            ).order_by(BookmarkModel.position_y)

            result = await self.session.execute(stmt)
            bookmarks = result.scalars().all()

            logger.info(
                f"Found {len(bookmarks)} bookmarks for page {page_number}")
            return list(bookmarks)
        except Exception as e:
            logger.error(f"Error getting bookmarks by page: {e}")
            raise

    async def get_by_user_and_document(
        self,
        user_id: str,
        document_id: str
    ) -> List[BookmarkModel]:
        """
        Get all bookmarks for a user in a specific document.

        Args:
            user_id: User ID
            document_id: Document ID

        Returns:
            List of bookmark models
        """
        try:
            stmt = select(BookmarkModel).where(
                and_(
                    BookmarkModel.user_id == user_id,
                    BookmarkModel.document_id == document_id
                )
            ).order_by(BookmarkModel.page_number, BookmarkModel.position_y)

            result = await self.session.execute(stmt)
            bookmarks = result.scalars().all()

            logger.info(
                f"Found {len(bookmarks)} bookmarks for user {user_id} in document {document_id}")
            return list(bookmarks)
        except Exception as e:
            logger.error(f"Error getting bookmarks by user and document: {e}")
            raise

    async def search_by_text(
        self,
        user_id: str,
        search_text: str,
        document_id: Optional[str] = None
    ) -> List[BookmarkModel]:
        """
        Search bookmarks by text content.

        Args:
            user_id: User ID
            search_text: Text to search for
            document_id: Optional document ID filter

        Returns:
            List of matching bookmark models
        """
        try:
            conditions = [BookmarkModel.user_id == user_id]

            if document_id:
                conditions.append(BookmarkModel.document_id == document_id)

            # Search in selected_text, ai_summary, title, and user_notes
            search_pattern = f"%{search_text}%"
            text_conditions = [
                BookmarkModel.selected_text.ilike(search_pattern),
                BookmarkModel.ai_summary.ilike(search_pattern),
                BookmarkModel.title.ilike(search_pattern),
                BookmarkModel.user_notes.ilike(search_pattern)
            ]

            from sqlalchemy import or_
            conditions.append(or_(*text_conditions))

            stmt = select(BookmarkModel).where(
                and_(*conditions)
            ).order_by(BookmarkModel.created_at.desc())

            result = await self.session.execute(stmt)
            bookmarks = result.scalars().all()

            logger.info(
                f"Found {len(bookmarks)} bookmarks matching '{search_text}'")
            return list(bookmarks)
        except Exception as e:
            logger.error(f"Error searching bookmarks: {e}")
            raise

    async def count_by_user(self, user_id: str) -> int:
        """
        Count total bookmarks for a user.

        Args:
            user_id: User ID

        Returns:
            Total count
        """
        try:
            from sqlalchemy import func
            stmt = select(func.count()).select_from(BookmarkModel).where(
                BookmarkModel.user_id == user_id
            )
            result = await self.session.execute(stmt)
            count = result.scalar()

            logger.info(f"User {user_id} has {count} bookmarks")
            return count or 0
        except Exception as e:
            logger.error(f"Error counting bookmarks: {e}")
            raise

    async def count_by_document(self, document_id: str, user_id: Optional[str] = None) -> int:
        """
        Count bookmarks for a document.

        Args:
            document_id: Document ID
            user_id: Optional user ID filter

        Returns:
            Total count
        """
        try:
            from sqlalchemy import func
            conditions = [BookmarkModel.document_id == document_id]

            if user_id:
                conditions.append(BookmarkModel.user_id == user_id)

            stmt = select(func.count()).select_from(BookmarkModel).where(
                and_(*conditions)
            )
            result = await self.session.execute(stmt)
            count = result.scalar()

            logger.info(f"Document {document_id} has {count} bookmarks")
            return count or 0
        except Exception as e:
            logger.error(f"Error counting document bookmarks: {e}")
            raise
