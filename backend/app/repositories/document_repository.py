"""
Document repository for database operations.

This module provides data access methods for Document entities,
including CRUD operations and custom queries.
"""

from typing import Optional, List
from uuid import UUID
from datetime import datetime

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from .base_repository import BaseRepository
# Import from __init__ to use the correct model
from ..models.db import DocumentModel
from ..models.domain.document import DocumentStatus
from ..core.logging import get_logger

logger = get_logger(__name__)


class DocumentRepository(BaseRepository[DocumentModel]):
    """
    Repository for Document database operations.

    Provides methods for creating, reading, updating, and deleting
    document records, as well as custom queries specific to documents.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize document repository.

        Args:
            session: Async database session
        """
        super().__init__(DocumentModel, session)

    async def get_by_hash(self, content_hash: str) -> Optional[DocumentModel]:
        """
        Get document by content hash.

        Args:
            content_hash: SHA-256 hash of document content

        Returns:
            Document model or None if not found
        """
        result = await self.session.execute(
            select(DocumentModel).where(
                DocumentModel.content_hash == content_hash)
        )
        doc = result.scalar_one_or_none()

        if doc:
            logger.debug(f"Found document with hash: {content_hash[:16]}...")
        else:
            logger.debug(
                f"No document found with hash: {content_hash[:16]}...")

        return doc

    async def get_by_filename(self, filename: str) -> Optional[DocumentModel]:
        """
        Get document by filename.

        Args:
            filename: Original filename

        Returns:
            Document model or None if not found
        """
        result = await self.session.execute(
            select(DocumentModel).where(DocumentModel.filename == filename)
        )
        return result.scalar_one_or_none()

    async def get_by_status(
        self,
        status: DocumentStatus,
        skip: int = 0,
        limit: int = 100
    ) -> List[DocumentModel]:
        """
        Get documents by processing status.

        Args:
            status: Document processing status
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of documents with specified status
        """
        result = await self.session.execute(
            select(DocumentModel)
            .where(DocumentModel.status == status)
            .order_by(DocumentModel.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        docs = result.scalars().all()
        logger.debug(f"Found {len(docs)} documents with status: {status}")
        return list(docs)

    async def update_status(
        self,
        id: UUID,
        status: DocumentStatus,
        error: Optional[str] = None
    ) -> Optional[DocumentModel]:
        """
        Update document processing status.

        Args:
            id: Document UUID
            status: New processing status
            error: Optional error message

        Returns:
            Updated document or None if not found
        """
        values = {"status": status}

        if status == DocumentStatus.PROCESSING:
            values["processing_started_at"] = datetime.utcnow()
        elif status in (DocumentStatus.COMPLETED, DocumentStatus.FAILED):
            values["processing_completed_at"] = datetime.utcnow()

        if error:
            values["processing_error"] = error

        doc = await self.update(id, values)

        if doc:
            logger.info(f"Updated document {id} status to: {status}")

        return doc

    async def update_chunk_count(self, id: UUID, chunk_count: int) -> Optional[DocumentModel]:
        """
        Update document chunk count.

        Args:
            id: Document UUID
            chunk_count: Number of chunks

        Returns:
            Updated document or None if not found
        """
        return await self.update(id, {"chunk_count": chunk_count})

    async def get_recent(self, limit: int = 10) -> List[DocumentModel]:
        """
        Get recently uploaded documents.

        Args:
            limit: Maximum number of documents to return

        Returns:
            List of recent documents
        """
        result = await self.session.execute(
            select(DocumentModel)
            .order_by(DocumentModel.created_at.desc())
            .limit(limit)
        )
        docs = result.scalars().all()
        logger.debug(f"Retrieved {len(docs)} recent documents")
        return list(docs)

    async def get_statistics(self) -> dict:
        """
        Get document statistics.

        Returns:
            Dictionary with statistics:
                - total: Total number of documents
                - by_status: Count by status
                - total_size: Total size in bytes
        """
        # Total count
        total_result = await self.session.execute(
            select(func.count()).select_from(DocumentModel)
        )
        total = total_result.scalar_one()

        # Count by status
        by_status = {}
        for status in DocumentStatus:
            status_result = await self.session.execute(
                select(func.count())
                .select_from(DocumentModel)
                .where(DocumentModel.status == status)
            )
            by_status[status.value] = status_result.scalar_one()

        # Total size
        size_result = await self.session.execute(
            select(func.sum(DocumentModel.file_size))
        )
        total_size = size_result.scalar_one() or 0

        stats = {
            "total": total,
            "by_status": by_status,
            "total_size": total_size
        }

        logger.info(f"Document statistics: {stats}")
        return stats

    async def delete_with_chunks(self, id: UUID) -> bool:
        """
        Delete document and all associated chunks.

        This uses cascade delete configured in the model relationships.

        Args:
            id: Document UUID

        Returns:
            True if deleted, False if not found
        """
        # The cascade delete will handle chunks automatically
        deleted = await self.delete(id)

        if deleted:
            logger.info(f"Deleted document {id} with all associated chunks")

        return deleted
