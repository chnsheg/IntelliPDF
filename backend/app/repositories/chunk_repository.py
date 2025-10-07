"""
Chunk repository for database operations.

This module provides data access methods for Chunk entities,
including CRUD operations and custom queries.
"""

from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .base_repository import BaseRepository
# Import from __init__ to use the correct models
from ..models.db import ChunkModel, DocumentModel
from ..models.domain.chunk import ChunkType
from ..core.logging import get_logger

logger = get_logger(__name__)


class ChunkRepository(BaseRepository[ChunkModel]):
    """
    Repository for Chunk database operations.

    Provides methods for creating, reading, updating, and deleting
    chunk records, as well as custom queries specific to chunks.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize chunk repository.

        Args:
            session: Async database session
        """
        super().__init__(ChunkModel, session)

    async def get_by_document_id(
        self,
        document_id: UUID,
        skip: int = 0,
        limit: int = 1000
    ) -> List[ChunkModel]:
        """
        Get all chunks for a document.

        Args:
            document_id: Document UUID
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of chunks for the document
        """
        # CRITICAL FIX: Convert UUID to string for SQLite compatibility
        doc_id_str = str(document_id) if isinstance(
            document_id, UUID) else document_id

        result = await self.session.execute(
            select(ChunkModel)
            .where(ChunkModel.document_id == doc_id_str)
            .order_by(ChunkModel.chunk_index)
            .offset(skip)
            .limit(limit)
        )
        chunks = result.scalars().all()
        logger.debug(f"Found {len(chunks)} chunks for document: {document_id}")
        return list(chunks)

    async def get_by_vector_id(self, vector_id: str) -> Optional[ChunkModel]:
        """
        Get chunk by vector database ID.

        Args:
            vector_id: Vector database ID

        Returns:
            Chunk model or None if not found
        """
        result = await self.session.execute(
            select(ChunkModel).where(ChunkModel.vector_id == vector_id)
        )
        chunk = result.scalar_one_or_none()

        if chunk:
            logger.debug(f"Found chunk with vector_id: {vector_id}")

        return chunk

    async def get_by_page_numbers(
        self,
        document_id: UUID,
        start_page: int,
        end_page: int
    ) -> List[ChunkModel]:
        """
        Get chunks by page number range.

        Args:
            document_id: Document UUID
            start_page: Start page number (inclusive)
            end_page: End page number (inclusive)

        Returns:
            List of chunks in the page range
        """
        # CRITICAL FIX: Convert UUID to string for SQLite compatibility
        doc_id_str = str(document_id) if isinstance(
            document_id, UUID) else document_id

        result = await self.session.execute(
            select(ChunkModel)
            .where(
                and_(
                    ChunkModel.document_id == doc_id_str,
                    ChunkModel.start_page >= start_page,
                    ChunkModel.end_page <= end_page
                )
            )
            .order_by(ChunkModel.chunk_index)
        )
        chunks = result.scalars().all()
        logger.debug(
            f"Found {len(chunks)} chunks for document {document_id} "
            f"in pages {start_page}-{end_page}"
        )
        return list(chunks)

    async def get_by_type(
        self,
        document_id: UUID,
        chunk_type: ChunkType
    ) -> List[ChunkModel]:
        """
        Get chunks by type.

        Args:
            document_id: Document UUID
            chunk_type: Chunk type

        Returns:
            List of chunks with specified type
        """
        # CRITICAL FIX: Convert UUID to string for SQLite compatibility
        doc_id_str = str(document_id) if isinstance(
            document_id, UUID) else document_id

        result = await self.session.execute(
            select(ChunkModel)
            .where(
                and_(
                    ChunkModel.document_id == doc_id_str,
                    ChunkModel.chunk_type == chunk_type
                )
            )
            .order_by(ChunkModel.chunk_index)
        )
        chunks = result.scalars().all()
        logger.debug(
            f"Found {len(chunks)} {chunk_type.value} chunks for document: {document_id}"
        )
        return list(chunks)

    async def create_batch(self, chunks: List[ChunkModel]) -> List[ChunkModel]:
        """
        Create multiple chunks in batch.

        Args:
            chunks: List of chunk models to create

        Returns:
            List of created chunks with database-generated values
        """
        self.session.add_all(chunks)
        await self.session.flush()

        # Refresh all objects to get generated IDs
        for chunk in chunks:
            await self.session.refresh(chunk)

        logger.info(f"Created {len(chunks)} chunks in batch")
        return chunks

    async def update_vector_id(
        self,
        chunk_id: UUID,
        vector_id: str
    ) -> Optional[ChunkModel]:
        """
        Update chunk with vector database ID.

        Args:
            chunk_id: Chunk UUID
            vector_id: Vector database ID

        Returns:
            Updated chunk or None if not found
        """
        chunk = await self.update(chunk_id, {"vector_id": vector_id})

        if chunk:
            logger.debug(
                f"Updated chunk {chunk_id} with vector_id: {vector_id}")

        return chunk

    async def update_vector_ids_batch(
        self,
        chunk_vector_pairs: List[tuple[UUID, str]]
    ) -> int:
        """
        Update multiple chunks with vector IDs in batch.

        Args:
            chunk_vector_pairs: List of (chunk_id, vector_id) tuples

        Returns:
            Number of chunks updated
        """
        updated_count = 0

        for chunk_id, vector_id in chunk_vector_pairs:
            chunk = await self.update_vector_id(chunk_id, vector_id)
            if chunk:
                updated_count += 1

        logger.info(f"Updated {updated_count} chunks with vector IDs in batch")
        return updated_count

    async def delete_by_document_id(self, document_id: UUID) -> int:
        """
        Delete all chunks for a document.

        Args:
            document_id: Document UUID

        Returns:
            Number of chunks deleted
        """
        # CRITICAL FIX: Convert UUID to string for SQLite compatibility
        doc_id_str = str(document_id) if isinstance(
            document_id, UUID) else document_id

        # Get all chunk IDs first
        result = await self.session.execute(
            select(ChunkModel.id).where(ChunkModel.document_id == doc_id_str)
        )
        chunk_ids = result.scalars().all()

        # Delete all chunks
        deleted_count = 0
        for chunk_id in chunk_ids:
            if await self.delete(chunk_id):
                deleted_count += 1

        logger.info(
            f"Deleted {deleted_count} chunks for document: {document_id}")
        return deleted_count

    async def get_chunk_statistics(self, document_id: UUID) -> dict:
        """
        Get chunk statistics for a document.

        Args:
            document_id: Document UUID

        Returns:
            Dictionary with statistics:
                - total: Total number of chunks
                - by_type: Count by chunk type
                - avg_length: Average chunk length
                - total_tokens: Total tokens across all chunks
        """
        from sqlalchemy import func

        # CRITICAL FIX: Convert UUID to string for SQLite compatibility
        doc_id_str = str(document_id) if isinstance(
            document_id, UUID) else document_id

        # Total count
        total_result = await self.session.execute(
            select(func.count())
            .select_from(ChunkModel)
            .where(ChunkModel.document_id == doc_id_str)
        )
        total = total_result.scalar_one()

        # Count by type
        by_type = {}
        for chunk_type in ChunkType:
            type_result = await self.session.execute(
                select(func.count())
                .select_from(ChunkModel)
                .where(
                    and_(
                        ChunkModel.document_id == doc_id_str,
                        ChunkModel.chunk_type == chunk_type
                    )
                )
            )
            by_type[chunk_type.value] = type_result.scalar_one()

        # Average length
        avg_result = await self.session.execute(
            select(func.avg(func.length(ChunkModel.content)))
            .where(ChunkModel.document_id == doc_id_str)
        )
        avg_length = avg_result.scalar_one() or 0

        # Total tokens
        tokens_result = await self.session.execute(
            select(func.sum(ChunkModel.token_count))
            .where(ChunkModel.document_id == doc_id_str)
        )
        total_tokens = tokens_result.scalar_one() or 0

        stats = {
            "total": total,
            "by_type": by_type,
            "avg_length": int(avg_length),
            "total_tokens": total_tokens
        }

        logger.debug(f"Chunk statistics for document {document_id}: {stats}")
        return stats

    async def search_by_content(
        self,
        document_id: UUID,
        search_text: str,
        limit: int = 10
    ) -> List[ChunkModel]:
        """
        Search chunks by content text.

        Args:
            document_id: Document UUID
            search_text: Text to search for
            limit: Maximum number of results

        Returns:
            List of matching chunks
        """
        # CRITICAL FIX: Convert UUID to string for SQLite compatibility
        doc_id_str = str(document_id) if isinstance(
            document_id, UUID) else document_id

        result = await self.session.execute(
            select(ChunkModel)
            .where(
                and_(
                    ChunkModel.document_id == doc_id_str,
                    ChunkModel.content.ilike(f"%{search_text}%")
                )
            )
            .order_by(ChunkModel.chunk_index)
            .limit(limit)
        )
        chunks = result.scalars().all()
        logger.debug(f"Found {len(chunks)} chunks matching '{search_text}'")
        return list(chunks)
