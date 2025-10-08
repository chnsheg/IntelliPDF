"""
Annotation repository for database operations.

Provides CRUD methods for annotations.
"""

from typing import Optional, List
from sqlalchemy import select, and_

from .base_repository import BaseRepository
from ..models.db import AnnotationModel
from ..core.logging import get_logger

logger = get_logger(__name__)


class AnnotationRepository(BaseRepository[AnnotationModel]):
    def __init__(self, session):
        super().__init__(AnnotationModel, session)

    async def get_by_document(self, document_id: str, user_id: Optional[str] = None) -> List[AnnotationModel]:
        try:
            stmt = select(AnnotationModel).where(
                AnnotationModel.document_id == document_id)
            if user_id:
                stmt = stmt.where(AnnotationModel.user_id == user_id)

            stmt = stmt.order_by(AnnotationModel.page_number,
                                 AnnotationModel.created_at)
            result = await self.session.execute(stmt)
            rows = result.scalars().all()
            logger.info(
                f"Found {len(rows)} annotations for document: {document_id}")
            return list(rows)
        except Exception as e:
            logger.error(f"Error getting annotations by document: {e}")
            raise
