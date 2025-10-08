"""
Document management endpoints.

Handles document upload, retrieval, processing, and chat operations.
"""

import time
from pathlib import Path
from typing import List, Optional, Dict, Any
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    UploadFile,
    File,
    BackgroundTasks,
    Request
)
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from ....core.config import get_settings
from ....core.dependencies import get_db
from ....core.logging import get_logger
from ....repositories.document_repository import DocumentRepository
from ....repositories.chunk_repository import ChunkRepository
from ....services.document_processing_service import DocumentProcessingService
from ....services.ai.embeddings import EmbeddingsService
from ....services.ai.retrieval import RetrievalService
from ....services.ai.llm import LLMService
from ....schemas.document import (
    DocumentResponse,
    DocumentListResponse,
    DocumentStatistics,
)
from ....schemas.chunk import ChunkResponse, ChunkListResponse, BoundingBox
from ....schemas.chat import ChatRequest, ChatResponse
from ....schemas.common import StatusResponse

logger = get_logger(__name__)
settings = get_settings()
router = APIRouter()


async def get_document_service(
    db: AsyncSession = Depends(get_db)
) -> DocumentProcessingService:
    """
    Get document processing service with dependencies.

    Args:
        db: Database session

    Returns:
        Document processing service instance
    """
    doc_repo = DocumentRepository(db)
    chunk_repo = ChunkRepository(db)
    embedding_service = EmbeddingsService()
    retrieval_service = RetrievalService()

    return DocumentProcessingService(
        document_repo=doc_repo,
        chunk_repo=chunk_repo,
        embedding_service=embedding_service,
        retrieval_service=retrieval_service,
    )


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
    service: DocumentProcessingService = Depends(get_document_service),
) -> DocumentResponse:
    """
    Upload and process a PDF document.

    This endpoint:
    1. Saves the uploaded file
    2. Parses the PDF
    3. Chunks the content
    4. Generates embeddings
    5. Stores in vector database

    Args:
        file: Uploaded PDF file
        background_tasks: Background tasks for async processing
        service: Document processing service

    Returns:
        Created document details

    Raises:
        HTTPException: If file is invalid or processing fails
    """
    # Validate file type
    if not file.filename.endswith('.pdf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported"
        )

    # Save uploaded file
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)

    file_path = upload_dir / file.filename

    try:
        # Write file to disk
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        logger.info(f"Uploaded file saved: {file_path}")

        # Process document
        # TEMPORARY: Disable embeddings due to ChromaDB compatibility issues
        document, chunks = await service.process_document(
            file_path=file_path,
            filename=file.filename,
            use_cache=True,
            chunk_strategy="section",
            generate_embeddings=False,  # Disabled temporarily
        )

        logger.info(f"Document processed successfully: {document.id}")

        # DEBUG: Check what we're getting
        logger.debug(
            f"document.doc_metadata type: {type(document.doc_metadata)}")
        logger.debug(f"document.doc_metadata value: {document.doc_metadata}")
        logger.debug(f"hasattr metadata: {hasattr(document, 'metadata')}")
        if hasattr(document, 'metadata'):
            logger.debug(f"document.metadata type: {type(document.metadata)}")

        # Manually construct DocumentResponse to avoid SQLAlchemy metadata conflict
        # CRITICAL:
        # - DocumentResponse field is 'doc_metadata' with alias='metadata'
        # - Pydantic requires using the ALIAS when constructing: metadata= (not doc_metadata=)
        # - Database model has 'doc_metadata' field, document.metadata is SQLAlchemy internal
        return DocumentResponse(
            id=document.id,
            filename=document.filename,
            file_path=document.file_path,
            file_size=document.file_size,
            content_hash=document.content_hash,
            status=document.status,
            processing_started_at=document.processing_started_at,
            processing_completed_at=document.processing_completed_at,
            processing_error=document.processing_error,
            chunk_count=document.chunk_count,
            # Use ALIAS 'metadata' with DATABASE FIELD 'doc_metadata'
            metadata=document.doc_metadata or {},
            created_at=document.created_at,
            updated_at=document.updated_at,
        )

    except Exception as e:
        logger.error(f"Failed to upload document: {str(e)}", exc_info=True)

        # Clean up file on error
        if file_path.exists():
            file_path.unlink()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process document: {str(e)}"
        )


@router.get("/", response_model=DocumentListResponse)
async def list_documents(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
) -> DocumentListResponse:
    """
    List all documents with pagination.

    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        db: Database session

    Returns:
        List of documents with pagination info
    """
    doc_repo = DocumentRepository(db)

    # Get documents
    documents = await doc_repo.get_all(skip=skip, limit=limit)
    total = await doc_repo.count()

    # Manually construct responses to avoid SQLAlchemy metadata conflict
    doc_responses = [
        DocumentResponse(
            id=doc.id,
            filename=doc.filename,
            file_path=doc.file_path,
            file_size=doc.file_size,
            content_hash=doc.content_hash,
            status=doc.status,
            processing_started_at=doc.processing_started_at,
            processing_completed_at=doc.processing_completed_at,
            processing_error=doc.processing_error,
            chunk_count=doc.chunk_count,
            metadata=doc.doc_metadata or {},
            created_at=doc.created_at,
            updated_at=doc.updated_at,
        )
        for doc in documents
    ]

    return DocumentListResponse(
        total=total,
        skip=skip,
        limit=limit,
        documents=doc_responses
    )


@router.get("/statistics", response_model=DocumentStatistics)
async def get_statistics(
    db: AsyncSession = Depends(get_db)
) -> DocumentStatistics:
    """
    Get document statistics.

    Args:
        db: Database session

    Returns:
        Document statistics
    """
    doc_repo = DocumentRepository(db)
    stats = await doc_repo.get_statistics()
    return DocumentStatistics(**stats)


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> DocumentResponse:
    """
    Get document by ID.

    Args:
        document_id: Document unique identifier
        db: Database session

    Returns:
        Document details

    Raises:
        HTTPException: If document not found
    """
    doc_repo = DocumentRepository(db)
    document = await doc_repo.get_by_id(document_id)

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found"
        )

    # Manually construct response to avoid SQLAlchemy metadata conflict
    return DocumentResponse(
        id=document.id,
        filename=document.filename,
        file_path=document.file_path,
        file_size=document.file_size,
        content_hash=document.content_hash,
        status=document.status,
        processing_started_at=document.processing_started_at,
        processing_completed_at=document.processing_completed_at,
        processing_error=document.processing_error,
        chunk_count=document.chunk_count,
        metadata=document.doc_metadata or {},
        created_at=document.created_at,
        updated_at=document.updated_at,
    )


@router.delete("/{document_id}", response_model=StatusResponse)
async def delete_document(
    document_id: UUID,
    service: DocumentProcessingService = Depends(get_document_service),
) -> StatusResponse:
    """
    Delete document by ID.

    This will delete:
    - Document record
    - All chunks
    - Vector embeddings
    - Physical file

    Args:
        document_id: Document unique identifier
        service: Document processing service

    Returns:
        Status response

    Raises:
        HTTPException: If document not found
    """
    deleted = await service.delete_document(document_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found"
        )

    return StatusResponse(
        success=True,
        message=f"Document {document_id} deleted successfully"
    )


@router.get("/{document_id}/chunks", response_model=ChunkListResponse)
async def get_document_chunks(
    document_id: UUID,
    skip: int = 0,
    limit: int = 1000,
    db: AsyncSession = Depends(get_db)
) -> ChunkListResponse:
    """
    Get all chunks for a document.

    Args:
        document_id: Document unique identifier
        skip: Number of records to skip
        limit: Maximum number of records to return
        db: Database session

    Returns:
        List of chunks

    Raises:
        HTTPException: If document not found
    """
    doc_repo = DocumentRepository(db)
    chunk_repo = ChunkRepository(db)

    # Check if document exists
    document = await doc_repo.get_by_id(document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found"
        )

    # Get chunks
    chunks = await chunk_repo.get_by_document_id(document_id, skip=skip, limit=limit)

    # Manually construct chunk responses to avoid SQLAlchemy metadata mapping issues
    chunk_responses = []
    for chunk in chunks:
        # Extract bounding boxes from metadata if available
        bounding_boxes = []
        if chunk.chunk_metadata and 'bounding_boxes' in chunk.chunk_metadata:
            bboxes = chunk.chunk_metadata['bounding_boxes']
            if isinstance(bboxes, list):
                bounding_boxes = [BoundingBox(
                    **bbox) if isinstance(bbox, dict) else bbox for bbox in bboxes]

        chunk_responses.append(ChunkResponse(
            id=chunk.id,
            document_id=chunk.document_id,
            content=chunk.content,
            chunk_index=chunk.chunk_index,
            chunk_type=chunk.chunk_type,
            start_page=chunk.start_page,
            end_page=chunk.end_page,
            token_count=chunk.token_count,
            vector_id=chunk.vector_id,
            bounding_boxes=bounding_boxes,
            chunk_metadata=chunk.chunk_metadata or {},
            created_at=chunk.created_at,
            updated_at=chunk.updated_at,
        ))

    return ChunkListResponse(
        document_id=document_id,
        total=len(chunks),
        chunks=chunk_responses
    )


@router.post("/{document_id}/chat", response_model=ChatResponse)
async def chat_with_document(
    document_id: UUID,
    payload: ChatRequest,
    request_obj: Request = None,
    db: AsyncSession = Depends(get_db)
) -> ChatResponse:
    """
    Ask questions about a document using RAG.

    This endpoint:
    1. Retrieves relevant chunks using vector search
    2. Generates answer using Gemini LLM
    3. Returns answer with source chunks

    Args:
        document_id: Document unique identifier
        request: Chat request with question and parameters
        db: Database session

    Returns:
        Generated answer with sources

    Raises:
        HTTPException: If document not found or processing fails
    """
    # Log incoming request for debugging
    logger.info(f"Chat request received: document_id={document_id}")
    # Log summary of parsed payload
    try:
        q_preview = payload.question[:50] if payload.question else ''
    except Exception:
        q_preview = '<unavailable>'

    logger.info(f"Request data: question='{q_preview}...', "
                f"top_k={payload.top_k}, temperature={payload.temperature}, "
                f"history_len={len(payload.conversation_history) if payload.conversation_history else 0}")

    # Also attempt to log raw JSON body for debugging frontend 422 issues
    if request_obj is not None:
        try:
            raw = await request_obj.json()
            logger.debug(f"Chat raw request body: {raw}")
        except Exception as e:
            logger.debug(f"Failed to read raw request body: {e}")

    start_time = time.time()

    doc_repo = DocumentRepository(db)

    # Check if document exists
    document = await doc_repo.get_by_id(document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found"
        )

    try:
        # Initialize services
        retrieval_service = RetrievalService()
        llm_service = LLMService()

        # Get collection name (use filename)
        collection_name = document.filename

        # Retrieve relevant chunks
        results = retrieval_service.search_by_document(
            query_text=payload.question,
            document_id=str(document_id),
            n_results=payload.top_k,
        )

        # RetrievalService.search_by_document returns a list of formatted result dicts
        # each with keys: 'id', 'text' (or 'content'), 'metadata', 'distance'.
        # Debug: log raw retrieval results to help diagnose missing fields
        logger.debug(f"Retrieval results raw: {results}")

        if not results:
            # Instead of returning a 404 (which the frontend surfaces as "Not Found"),
            # return a structured ChatResponse indicating no relevant content was found.
            # This is friendlier for the UI and avoids confusing 404 behavior when the
            # document exists but the retrieval index (vector DB) has no matches.
            logger.warning(
                f"No retrieval results for document={document_id}; returning empty chat response")
            return ChatResponse(
                answer="未能找到与问题相关的文档内容。请尝试缩短或更换问题，或确认文档已正确索引/嵌入。",
                sources=[],
                document_id=document_id,
                question=payload.question if hasattr(
                    payload, 'question') else "",
                processing_time=0.0,
            )

        # Normalize results into lists of docs/metadatas/distances
        # Some result entries may use 'text' or 'content'
        retrieved_docs = [r.get('text') or r.get(
            'content') or '' for r in results]
        metadatas = [r.get('metadata', {}) for r in results]
        distances = [r.get('distance', None) for r in results]

        # Prepare context
        context = "\n\n".join(retrieved_docs)

        # Generate answer using LLMService.answer_question (RAG)
        answer_result = await llm_service.answer_question(
            question=payload.question,
            document_id=str(document_id),
            n_contexts=payload.top_k,
            language=payload.language if hasattr(
                payload, 'language') else 'zh',
            temperature=payload.temperature,
        )

        # The service returns a dict with 'answer' and 'contexts'
        answer = answer_result.get('answer') if isinstance(
            answer_result, dict) else answer_result

        # Prepare sources from original results to ensure chunk_id is present
        sources = []
        for r in results:
            meta = r.get('metadata') or {}
            text = r.get('text') or ""
            dist = r.get('distance')
            # Prefer explicit id from result; fallback to document_id + chunk_index
            chunk_id = r.get('id')
            if not chunk_id:
                chunk_index = meta.get('chunk_index')
                if chunk_index is not None:
                    chunk_id = f"{document_id}_{chunk_index}"
                else:
                    chunk_id = ""

            content_snippet = text[:200] + \
                "..." if isinstance(text, str) and len(text) > 200 else text
            similarity = (1 - dist) if (isinstance(dist,
                                                   (int, float)) and dist is not None) else 0

            # Build source object and include frontend-friendly aliases
            page_val = None
            # Prefer metadata start_page, then 'page', then first of page_numbers
            if meta:
                if meta.get('start_page') is not None:
                    page_val = meta.get('start_page')
                elif meta.get('page') is not None:
                    page_val = meta.get('page')
                elif meta.get('page_numbers'):
                    try:
                        page_nums = meta.get('page_numbers')
                        # page_numbers might be a list or a string representation
                        if isinstance(page_nums, (list, tuple)) and len(page_nums) > 0:
                            page_val = int(page_nums[0])
                        elif isinstance(page_nums, str):
                            # attempt to parse digits
                            import re
                            m = re.search(r"\d+", page_nums)
                            if m:
                                page_val = int(m.group(0))
                    except Exception:
                        page_val = None

            similarity_val = None
            try:
                if similarity is not None:
                    similarity_val = float(similarity)
            except Exception:
                similarity_val = None

            sources.append({
                "chunk_id": chunk_id,
                "content": content_snippet,
                # original keys (keep for backward compatibility)
                "page": page_val,
                "similarity": similarity_val,
                # frontend-friendly aliases expected by React UI
                "page_number": page_val,
                "similarity_score": similarity_val,
            })

        processing_time = time.time() - start_time

        return ChatResponse(
            answer=answer,
            sources=sources,
            document_id=document_id,
            question=payload.question,
            processing_time=processing_time,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate answer: {str(e)}"
        )


@router.get("/{document_id}/file")
async def get_document_file(
    document_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> FileResponse:
    """
    Get the original PDF file for a document.

    Args:
        document_id: Document unique identifier
        db: Database session

    Returns:
        PDF file

    Raises:
        HTTPException: If document or file not found
    """
    doc_repo = DocumentRepository(db)
    document = await doc_repo.get_by_id(document_id)

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found"
        )

    file_path = Path(document.file_path)
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File not found: {document.file_path}"
        )

    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename=document.filename
    )


@router.get("/{document_id}/thumbnail")
async def get_document_thumbnail(
    document_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> FileResponse:
    """
    Get a thumbnail image for the first page of a document.

    Note: This is a placeholder implementation that returns a default image.
    Full implementation would require PDF-to-image conversion (e.g., using pdf2image).

    Args:
        document_id: Document unique identifier
        db: Database session

    Returns:
        PNG thumbnail image

    Raises:
        HTTPException: If document not found
    """
    doc_repo = DocumentRepository(db)
    document = await doc_repo.get_by_id(document_id)

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found"
        )

    # TODO: Implement actual thumbnail generation
    # For now, return the PDF file itself (browser can preview first page)
    file_path = Path(document.file_path)
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File not found: {document.file_path}"
        )

    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename=f"{document.filename}_thumbnail.pdf"
    )


@router.post("/{document_id}/current-context")
async def get_current_context(
    document_id: UUID,
    page: int,
    x: Optional[float] = None,
    y: Optional[float] = None,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get relevant chunk context based on current reading position.

    This endpoint finds chunks that overlap with the current page and position,
    which can be used for context-aware AI chat.

    Args:
        document_id: Document unique identifier
        page: Current page number (1-based)
        x: Optional X coordinate on page
        y: Optional Y coordinate on page
        db: Database session

    Returns:
        Current context information including relevant chunks

    Raises:
        HTTPException: If document not found
    """
    doc_repo = DocumentRepository(db)
    chunk_repo = ChunkRepository(db)

    # Check if document exists
    document = await doc_repo.get_by_id(document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found"
        )

    # Get all chunks for the document
    all_chunks = await chunk_repo.get_by_document_id(document_id, skip=0, limit=10000)

    # Filter chunks that are on or near the current page
    relevant_chunks = []
    for chunk in all_chunks:
        if chunk.start_page <= page <= chunk.end_page:
            # Calculate relevance score based on position
            relevance = 1.0

            # If coordinates provided, check if chunk overlaps with position
            if x is not None and y is not None and chunk.chunk_metadata:
                bboxes = chunk.chunk_metadata.get('bounding_boxes', [])
                for bbox in bboxes:
                    if (bbox.get('page') == page and
                        bbox.get('x0', 0) <= x <= bbox.get('x1', 999) and
                            bbox.get('y0', 0) <= y <= bbox.get('y1', 999)):
                        relevance = 2.0  # Higher relevance for position match
                        break

            relevant_chunks.append({
                'chunk_id': str(chunk.id),
                'chunk_index': chunk.chunk_index,
                'content': chunk.content,
                'chunk_type': chunk.chunk_type,
                'start_page': chunk.start_page,
                'end_page': chunk.end_page,
                'relevance': relevance,
                'bounding_boxes': chunk.chunk_metadata.get('bounding_boxes', []) if chunk.chunk_metadata else []
            })

    # Sort by relevance and page proximity
    relevant_chunks.sort(
        key=lambda c: (-c['relevance'], abs(c['start_page'] - page)))

    # Return top 5 most relevant chunks
    top_chunks = relevant_chunks[:5]

    return {
        'document_id': str(document_id),
        'current_page': page,
        'current_position': {'x': x, 'y': y} if x is not None and y is not None else None,
        'relevant_chunks': top_chunks,
        'total_found': len(relevant_chunks)
    }


@router.get("/{document_id}/chunks/{chunk_id}")
async def get_chunk_detail(
    document_id: UUID,
    chunk_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> ChunkResponse:
    """
    Get detailed information about a specific chunk.

    Args:
        document_id: Document unique identifier
        chunk_id: Chunk unique identifier
        db: Database session

    Returns:
        Detailed chunk information

    Raises:
        HTTPException: If document or chunk not found
    """
    doc_repo = DocumentRepository(db)
    chunk_repo = ChunkRepository(db)

    # Check if document exists
    document = await doc_repo.get_by_id(document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found"
        )

    # Get chunk
    chunk = await chunk_repo.get_by_id(chunk_id)
    if not chunk or str(chunk.document_id) != str(document_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chunk {chunk_id} not found in document {document_id}"
        )

    # Extract bounding boxes from metadata if available
    bounding_boxes = []
    if chunk.chunk_metadata and 'bounding_boxes' in chunk.chunk_metadata:
        bboxes = chunk.chunk_metadata['bounding_boxes']
        if isinstance(bboxes, list):
            bounding_boxes = [BoundingBox(
                **bbox) if isinstance(bbox, dict) else bbox for bbox in bboxes]

    return ChunkResponse(
        id=chunk.id,
        document_id=chunk.document_id,
        content=chunk.content,
        chunk_index=chunk.chunk_index,
        chunk_type=chunk.chunk_type,
        start_page=chunk.start_page,
        end_page=chunk.end_page,
        token_count=chunk.token_count,
        vector_id=chunk.vector_id,
        bounding_boxes=bounding_boxes,
        chunk_metadata=chunk.chunk_metadata or {},
        created_at=chunk.created_at,
        updated_at=chunk.updated_at,
    )
