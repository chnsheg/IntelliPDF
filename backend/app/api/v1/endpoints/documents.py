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
    BackgroundTasks
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
    request: ChatRequest,
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
        results = await retrieval_service.query(
            collection_name=collection_name,
            query_text=request.question,
            top_k=request.top_k,
        )

        if not results:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No relevant content found for this question"
            )

        # Extract documents and metadata
        retrieved_docs = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        # Prepare context
        context = "\n\n".join(retrieved_docs)

        # Generate answer
        answer = await llm_service.generate_answer(
            question=request.question,
            context=context,
            conversation_history=request.conversation_history,
            temperature=request.temperature,
        )

        # Prepare sources
        sources = [
            {
                "content": doc[:200] + "..." if len(doc) > 200 else doc,
                "page": meta.get("start_page", 0),
                "chunk_index": meta.get("chunk_index", 0),
                "similarity": 1 - dist if dist else 0,  # Convert distance to similarity
            }
            for doc, meta, dist in zip(retrieved_docs, metadatas, distances)
        ]

        processing_time = time.time() - start_time

        return ChatResponse(
            answer=answer,
            sources=sources,
            document_id=document_id,
            question=request.question,
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
    relevant_chunks.sort(key=lambda c: (-c['relevance'], abs(c['start_page'] - page)))

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
            bounding_boxes = [BoundingBox(**bbox) if isinstance(bbox, dict) else bbox for bbox in bboxes]

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
