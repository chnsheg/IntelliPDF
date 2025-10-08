"""
Annotation repository for database operations.

Provides CRUD methods for annotations with advanced filtering.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy import select, and_, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from .base_repository import BaseRepository
from ..models.db import AnnotationModel, AnnotationReplyModel
from ..core.logging import get_logger

logger = get_logger(__name__)


class AnnotationRepository(BaseRepository[AnnotationModel]):
    """Repository for annotation operations"""

    def __init__(self, session: AsyncSession):
        super().__init__(AnnotationModel, session)

    async def get_by_document(
        self,
        document_id: str,
        page_number: Optional[int] = None,
        annotation_type: Optional[str] = None,
        user_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 1000,
        offset: int = 0
    ) -> tuple[List[AnnotationModel], int]:
        """
        Get annotations for a document with optional filtering.
        Returns (annotations, total_count).
        """
        try:
            # Build WHERE clause
            conditions = [AnnotationModel.document_id == document_id]
            
            if page_number is not None:
                conditions.append(AnnotationModel.page_number == page_number)
            if annotation_type:
                conditions.append(AnnotationModel.annotation_type == annotation_type)
            if user_id:
                conditions.append(AnnotationModel.user_id == user_id)
            if tags:
                # Check if any of the provided tags exist in the annotation's tags JSON array
                for tag in tags:
                    conditions.append(AnnotationModel.tags.contains([tag]))

            # Count query
            count_stmt = select(func.count()).select_from(AnnotationModel).where(and_(*conditions))
            count_result = await self.session.execute(count_stmt)
            total = count_result.scalar() or 0

            # Data query
            stmt = (
                select(AnnotationModel)
                .where(and_(*conditions))
                .order_by(AnnotationModel.page_number, AnnotationModel.created_at)
                .limit(limit)
                .offset(offset)
            )
            result = await self.session.execute(stmt)
            annotations = list(result.scalars().all())

            logger.info(f"Found {len(annotations)}/{total} annotations for document: {document_id}")
            return annotations, total

        except Exception as e:
            logger.error(f"Error getting annotations by document: {e}")
            raise

    async def get_by_page(
        self,
        document_id: str,
        page_number: int
    ) -> List[AnnotationModel]:
        """Get all annotations for a specific page"""
        try:
            stmt = (
                select(AnnotationModel)
                .where(
                    and_(
                        AnnotationModel.document_id == document_id,
                        AnnotationModel.page_number == page_number
                    )
                )
                .order_by(AnnotationModel.created_at)
            )
            result = await self.session.execute(stmt)
            annotations = list(result.scalars().all())
            logger.info(f"Found {len(annotations)} annotations on page {page_number}")
            return annotations
        except Exception as e:
            logger.error(f"Error getting annotations by page: {e}")
            raise

    async def get_by_user(
        self,
        user_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> tuple[List[AnnotationModel], int]:
        """Get all annotations by a specific user"""
        try:
            # Count
            count_stmt = select(func.count()).select_from(AnnotationModel).where(
                AnnotationModel.user_id == user_id
            )
            count_result = await self.session.execute(count_stmt)
            total = count_result.scalar() or 0

            # Data
            stmt = (
                select(AnnotationModel)
                .where(AnnotationModel.user_id == user_id)
                .order_by(desc(AnnotationModel.created_at))
                .limit(limit)
                .offset(offset)
            )
            result = await self.session.execute(stmt)
            annotations = list(result.scalars().all())

            logger.info(f"Found {len(annotations)}/{total} annotations for user: {user_id}")
            return annotations, total
        except Exception as e:
            logger.error(f"Error getting annotations by user: {e}")
            raise

    async def batch_delete(self, annotation_ids: List[str]) -> int:
        """Delete multiple annotations by ID"""
        try:
            stmt = select(AnnotationModel).where(
                AnnotationModel.id.in_(annotation_ids)
            )
            result = await self.session.execute(stmt)
            annotations = list(result.scalars().all())
            
            count = 0
            for annotation in annotations:
                await self.session.delete(annotation)
                count += 1
            
            await self.session.commit()
            logger.info(f"Batch deleted {count} annotations")
            return count
        except Exception as e:
            logger.error(f"Error in batch delete: {e}")
            await self.session.rollback()
            raise

    async def get_statistics(self, document_id: str) -> Dict[str, Any]:
        """Get annotation statistics for a document"""
        try:
            # Total count
            total_stmt = select(func.count()).select_from(AnnotationModel).where(
                AnnotationModel.document_id == document_id
            )
            total_result = await self.session.execute(total_stmt)
            total = total_result.scalar() or 0

            # By type
            type_stmt = (
                select(
                    AnnotationModel.annotation_type,
                    func.count(AnnotationModel.id)
                )
                .where(AnnotationModel.document_id == document_id)
                .group_by(AnnotationModel.annotation_type)
            )
            type_result = await self.session.execute(type_stmt)
            by_type = {row[0]: row[1] for row in type_result.all()}

            # By page
            page_stmt = (
                select(
                    AnnotationModel.page_number,
                    func.count(AnnotationModel.id)
                )
                .where(AnnotationModel.document_id == document_id)
                .group_by(AnnotationModel.page_number)
            )
            page_result = await self.session.execute(page_stmt)
            by_page = {row[0]: row[1] for row in page_result.all()}

            return {
                "total_count": total,
                "by_type": by_type,
                "by_page": by_page
            }
        except Exception as e:
            logger.error(f"Error getting annotation statistics: {e}")
            raise


class AnnotationReplyRepository(BaseRepository[AnnotationReplyModel]):
    """Repository for annotation reply operations"""

    def __init__(self, session: AsyncSession):
        super().__init__(AnnotationReplyModel, session)

    async def get_by_annotation(
        self,
        annotation_id: str
    ) -> List[AnnotationReplyModel]:
        """Get all replies for an annotation"""
        try:
            stmt = (
                select(AnnotationReplyModel)
                .where(AnnotationReplyModel.annotation_id == annotation_id)
                .order_by(AnnotationReplyModel.created_at)
            )
            result = await self.session.execute(stmt)
            replies = list(result.scalars().all())
            logger.info(f"Found {len(replies)} replies for annotation: {annotation_id}")
            return replies
        except Exception as e:
            logger.error(f"Error getting replies: {e}")
            raise
