"""
Enhanced document endpoints with batch operations and advanced search.
"""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_

from ....core.dependencies import get_db
from ....core.logging import get_logger
from ....models.db import DocumentModel
from ....repositories.document_repository import DocumentRepository
from ....schemas.document import DocumentResponse
from ....schemas.common import StatusResponse
from pydantic import BaseModel

logger = get_logger(__name__)
router = APIRouter()


class BatchDeleteRequest(BaseModel):
    """Request to delete multiple documents."""
    document_ids: List[UUID]


class BatchOperationResponse(BaseModel):
    """Response for batch operations."""
    success: bool
    processed: int
    failed: int
    errors: List[str] = []


class SearchFilters(BaseModel):
    """Advanced search filters."""
    query: str | None = None
    status: str | None = None
    tags: List[str] = []
    date_from: str | None = None
    date_to: str | None = None
    min_pages: int | None = None
    max_pages: int | None = None


@router.post("/batch/delete", response_model=BatchOperationResponse)
async def batch_delete_documents(
    request: BatchDeleteRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Delete multiple documents in batch.

    - **document_ids**: List of document IDs to delete
    """
    repo = DocumentRepository(db)
    processed = 0
    failed = 0
    errors = []

    for doc_id in request.document_ids:
        try:
            doc = await repo.get_by_id(doc_id)
            if doc:
                await repo.delete(doc)
                processed += 1
            else:
                failed += 1
                errors.append(f"Document {doc_id} not found")
        except Exception as e:
            failed += 1
            errors.append(f"Error deleting {doc_id}: {str(e)}")
            logger.error(f"Batch delete error for {doc_id}: {e}")

    await db.commit()

    return BatchOperationResponse(
        success=failed == 0,
        processed=processed,
        failed=failed,
        errors=errors,
    )


@router.get("/search/advanced")
async def advanced_search(
    query: str | None = Query(None, description="Search query"),
    status_filter: str | None = Query(None, description="Document status"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", description="Sort order (asc/desc)"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """
    Advanced document search with filters and sorting.

    - **query**: Text search in title and filename
    - **status**: Filter by processing status
    - **sort_by**: Field to sort by (created_at, title, file_size)
    - **sort_order**: asc or desc
    - **limit**: Maximum results
    - **offset**: Pagination offset
    """
    stmt = select(DocumentModel)

    # Apply filters
    filters = []
    if query:
        search_pattern = f"%{query}%"
        filters.append(
            or_(
                DocumentModel.title.ilike(search_pattern),
                DocumentModel.original_filename.ilike(search_pattern),
            )
        )

    if status_filter:
        filters.append(DocumentModel.processing_status == status_filter)

    if filters:
        stmt = stmt.where(and_(*filters))

    # Apply sorting
    sort_column = getattr(DocumentModel, sort_by, DocumentModel.created_at)
    if sort_order.lower() == "desc":
        stmt = stmt.order_by(sort_column.desc())
    else:
        stmt = stmt.order_by(sort_column.asc())

    # Apply pagination
    stmt = stmt.limit(limit).offset(offset)

    result = await db.execute(stmt)
    documents = result.scalars().all()

    # Convert to dict for proper serialization
    return [
        {
            "id": str(doc.id),
            "filename": doc.original_filename,
            "file_path": doc.file_path,
            "file_size": doc.file_size,
            "content_hash": doc.content_hash,
            "status": doc.processing_status,
            "processing_started_at": doc.processing_started_at.isoformat() if doc.processing_started_at else None,
            "processing_completed_at": doc.processing_completed_at.isoformat() if doc.processing_completed_at else None,
            "processing_error": doc.processing_error,
            "metadata": doc.metadata or {},
            "chunk_count": doc.chunk_count or 0,
            "created_at": doc.created_at.isoformat(),
            "updated_at": doc.updated_at.isoformat(),
            "title": doc.title,
            "original_filename": doc.original_filename,
            "total_pages": doc.total_pages or 0,
            "processing_time": doc.processing_time or 0.0,
        }
        for doc in documents
    ]


@router.get("/statistics/detailed")
async def get_detailed_statistics(
    db: AsyncSession = Depends(get_db),
):
    """
    Get detailed document statistics.

    Returns comprehensive statistics including:
    - Total documents and chunks
    - Status breakdown
    - Storage usage
    - Processing time stats
    """
    # Total documents
    total_docs_stmt = select(func.count(DocumentModel.id))
    total_docs = (await db.execute(total_docs_stmt)).scalar()

    # Status breakdown
    status_stmt = select(
        DocumentModel.processing_status,
        func.count(DocumentModel.id)
    ).group_by(DocumentModel.processing_status)
    status_result = await db.execute(status_stmt)
    status_breakdown = {row[0]: row[1] for row in status_result}

    # Storage usage
    storage_stmt = select(func.sum(DocumentModel.file_size))
    total_storage = (await db.execute(storage_stmt)).scalar() or 0

    # Average processing time
    avg_time_stmt = select(func.avg(DocumentModel.processing_time))
    avg_processing_time = (await db.execute(avg_time_stmt)).scalar() or 0.0

    return {
        "total_documents": total_docs,
        "status_breakdown": status_breakdown,
        "total_storage_bytes": int(total_storage),
        "average_processing_time": float(avg_processing_time),
        "storage_formatted": _format_bytes(total_storage),
    }


def _format_bytes(bytes_size: int) -> str:
    """Format bytes to human-readable string."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.2f} TB"


@router.post("/{document_id}/tags")
async def add_document_tags(
    document_id: UUID,
    tags: List[str],
    db: AsyncSession = Depends(get_db),
):
    """
    Add tags to a document (future feature).

    Currently returns success for API compatibility.
    """
    # TODO: Implement tags in database schema
    return StatusResponse(
        success=True,
        message=f"Tags feature coming soon. Would add: {', '.join(tags)}",
    )


@router.get("/export/metadata")
async def export_documents_metadata(
    format: str = Query("json", description="Export format (json/csv)"),
    db: AsyncSession = Depends(get_db),
):
    """
    Export all documents metadata.

    - **format**: Output format (json or csv)
    """
    stmt = select(DocumentModel).order_by(DocumentModel.created_at.desc())
    result = await db.execute(stmt)
    documents = result.scalars().all()

    if format.lower() == "csv":
        # CSV export
        import io
        import csv

        output = io.StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=['id', 'title', 'filename',
                        'status', 'pages', 'created_at']
        )
        writer.writeheader()

        for doc in documents:
            writer.writerow({
                'id': str(doc.id),
                'title': doc.title,
                'filename': doc.original_filename,
                'status': doc.processing_status,
                'pages': doc.total_pages,
                'created_at': doc.created_at.isoformat(),
            })

        return {
            "format": "csv",
            "data": output.getvalue(),
        }
    else:
        # JSON export
        return {
            "format": "json",
            "data": [
                {
                    "id": str(doc.id),
                    "title": doc.title,
                    "filename": doc.original_filename,
                    "status": doc.processing_status,
                    "pages": doc.total_pages,
                    "file_size": doc.file_size,
                    "created_at": doc.created_at.isoformat(),
                }
                for doc in documents
            ],
        }
