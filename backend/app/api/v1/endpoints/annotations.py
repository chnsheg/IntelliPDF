"""
Annotation API endpoints.

Provides CRUD endpoints to create, list, update and delete annotations.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ....core.dependencies import get_db
from ....core.logging import get_logger
from ....schemas.annotation import (
    AnnotationCreate,
    AnnotationResponse,
    AnnotationListResponse,
    AnnotationUpdate,
)
from ....schemas.user import UserResponse
from ....repositories.annotation_repository import AnnotationRepository
from ...dependencies.auth import get_current_active_user

logger = get_logger(__name__)
router = APIRouter()


async def get_annotation_repo(db: AsyncSession = Depends(get_db)) -> AnnotationRepository:
    return AnnotationRepository(db)


@router.post(
    "/",
    response_model=AnnotationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_annotation(
    data: AnnotationCreate,
    current_user: UserResponse = Depends(get_current_active_user),
    repo: AnnotationRepository = Depends(get_annotation_repo),
):
    try:
        # Ensure user_id matches authenticated
        if data.user_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail="user_id mismatch")

        model = await repo.create(
            **{
                "document_id": data.document_id,
                "user_id": data.user_id,
                "annotation_type": data.annotation_type,
                "page_number": data.page_number,
                "position": data.position.dict() if data.position else None,
                "color": data.color,
                "content": data.content,
                "tags": data.tags or [],
            }
        )

        return model
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create annotation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get(
    "/documents/{document_id}",
    response_model=AnnotationListResponse,
)
async def get_annotations_for_document(
    document_id: str,
    current_user: UserResponse = Depends(get_current_active_user),
    repo: AnnotationRepository = Depends(get_annotation_repo),
):
    try:
        items = await repo.get_by_document(document_id=document_id, user_id=current_user.id)
        return AnnotationListResponse(annotations=items, total=len(items))
    except Exception as e:
        logger.error(f"Failed to get annotations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.put("/{annotation_id}", response_model=AnnotationResponse)
async def update_annotation(
    annotation_id: str,
    update: AnnotationUpdate,
    current_user: UserResponse = Depends(get_current_active_user),
    repo: AnnotationRepository = Depends(get_annotation_repo),
):
    try:
        model = await repo.get_by_id(annotation_id)
        if not model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
        if model.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

        # Apply updates
        data = {}
        if update.color is not None:
            data["color"] = update.color
        if update.content is not None:
            data["content"] = update.content
        if update.tags is not None:
            data["tags"] = update.tags

        updated = await repo.update(model, **data)
        return updated
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update annotation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/{annotation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_annotation(
    annotation_id: str,
    current_user: UserResponse = Depends(get_current_active_user),
    repo: AnnotationRepository = Depends(get_annotation_repo),
):
    try:
        model = await repo.get_by_id(annotation_id)
        if not model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
        if model.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

        await repo.delete(model)
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete annotation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
