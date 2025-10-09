"""
Annotation API endpoints.

Provides CRUD endpoints to create, list, update and delete annotations.
"""

from typing import Optional
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
from ....repositories.annotation_repository import AnnotationRepository

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
    repo: AnnotationRepository = Depends(get_annotation_repo),
):
    """Create a new PDF annotation"""
    try:
        # Create model instance from schema
        from ....models.db import AnnotationModel
        model = AnnotationModel(
            document_id=data.document_id,
            user_id=data.user_id,
            annotation_type=data.annotation_type,
            page_number=data.page_number,
            data=data.data,  # Store complete annotation data as JSON
            content=data.content,
            color=data.color,
            tags=data.tags,
            user_name=data.user_name,
        )

        # Save to database
        created_model = await repo.create(model)

        logger.info(
            f"Created annotation {created_model.id} for document {data.document_id}")
        return created_model
    except Exception as e:
        logger.error(f"Failed to create annotation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get(
    "/documents/{document_id}",
    response_model=AnnotationListResponse,
)
async def get_annotations_for_document(
    document_id: str,
    page_number: Optional[int] = None,
    annotation_type: Optional[str] = None,
    limit: int = 1000,
    offset: int = 0,
    repo: AnnotationRepository = Depends(get_annotation_repo),
):
    """Get all annotations for a document with optional filtering"""
    try:
        annotations, total = await repo.get_by_document(
            document_id=document_id,
            page_number=page_number,
            annotation_type=annotation_type,
            limit=limit,
            offset=offset
        )

        has_more = (offset + len(annotations)) < total
        page = offset // limit + 1 if limit > 0 else 1

        return AnnotationListResponse(
            annotations=annotations,
            total=total,
            page=page,
            page_size=limit,
            has_more=has_more
        )
    except Exception as e:
        logger.error(f"Failed to get annotations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.patch("/{annotation_id}", response_model=AnnotationResponse)
async def update_annotation(
    annotation_id: str,
    update: AnnotationUpdate,
    repo: AnnotationRepository = Depends(get_annotation_repo),
):
    """Update an existing annotation"""
    try:
        model = await repo.get_by_id(annotation_id)
        if not model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Annotation not found"
            )

        # Build update dictionary from non-None fields
        update_data = {}
        if update.data is not None:
            update_data["data"] = update.data
        if update.content is not None:
            update_data["content"] = update.content
        if update.color is not None:
            update_data["color"] = update.color
        if update.tags is not None:
            update_data["tags"] = update.tags

        updated = await repo.update(model, **update_data)
        logger.info(f"Updated annotation {annotation_id}")
        return updated
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update annotation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/{annotation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_annotation(
    annotation_id: str,
    repo: AnnotationRepository = Depends(get_annotation_repo),
):
    """Delete an annotation"""
    try:
        # Convert annotation_id to UUID if needed
        from uuid import UUID
        try:
            id_uuid = UUID(annotation_id) if isinstance(
                annotation_id, str) else annotation_id
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid annotation ID format"
            )

        # Check if annotation exists
        model = await repo.get_by_id(id_uuid)
        if not model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Annotation not found"
            )

        # Delete by ID, not by model instance
        deleted = await repo.delete(id_uuid)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete annotation"
            )

        logger.info(f"Deleted annotation {annotation_id}")
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete annotation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post(
    "/batch",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
)
async def batch_create_annotations(
    request: dict,
    repo: AnnotationRepository = Depends(get_annotation_repo),
):
    """
    批量创建标注（用于 PDF.js）

    请求格式:
    {
        "annotations": [
            {
                "document_id": "uuid",
                "user_id": "user_id",
                "annotation_type": "pdfjs",
                "page_number": 1,
                "data": { "pdfjs_data": {...} },
                "tags": []
            },
            ...
        ]
    }
    """
    try:
        annotations_data = request.get('annotations', [])
        if not annotations_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No annotations provided"
            )

        created_count = 0
        errors = []
        from ....models.db import AnnotationModel

        for i, ann_data in enumerate(annotations_data):
            try:
                # 验证必填字段
                required_fields = ['document_id',
                                   'user_id', 'page_number', 'data']
                missing = [f for f in required_fields if f not in ann_data]

                if missing:
                    error_msg = f"Item {i}: Missing {', '.join(missing)}"
                    errors.append(error_msg)
                    logger.warning(error_msg)
                    continue

                model = AnnotationModel(
                    document_id=ann_data['document_id'],
                    user_id=ann_data['user_id'],
                    annotation_type=ann_data.get('annotation_type', 'pdfjs'),
                    page_number=ann_data['page_number'],
                    data=ann_data['data'],
                    content=ann_data.get('content'),
                    color=ann_data.get('color'),
                    tags=ann_data.get('tags', []),
                    user_name=ann_data.get('user_name'),
                )
                await repo.create(model)
                created_count += 1

            except Exception as e:
                error_msg = f"Item {i}: {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)

        logger.info(
            f"Batch created {created_count}/{len(annotations_data)} annotations")

        result = {
            "status": "success" if created_count > 0 else "failed",
            "created": created_count,
            "total": len(annotations_data)
        }
        if errors:
            result["errors"] = errors

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to batch create annotations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete(
    "/documents/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_annotations_by_document(
    document_id: str,
    repo: AnnotationRepository = Depends(get_annotation_repo),
):
    """删除文档的所有标注"""
    try:
        # 使用 repository 的 get_by_document 方法
        annotations, total = await repo.get_by_document(
            document_id=document_id,
            limit=10000  # 一次性获取所有
        )

        # 删除所有标注
        deleted_count = 0
        for ann in annotations:
            await repo.delete(ann.id)
            deleted_count += 1

        logger.info(
            f"Deleted {deleted_count} annotations for document {document_id}")
        return None

    except Exception as e:
        logger.error(f"Failed to delete annotations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
