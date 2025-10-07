"""
Document processing service for coordinating PDF processing pipeline.

This service orchestrates the complete document processing workflow:
1. PDF parsing and extraction
2. Intelligent chunking
3. Embedding generation
4. Vector storage
5. Database persistence
"""

import hashlib
from pathlib import Path
from typing import Optional, List, Tuple
from uuid import UUID

from ..core.logging import get_logger
from ..core.exceptions import ProcessingError
from ..models.db import DocumentModel, ChunkModel  # Import from __init__
from ..models.domain.document import DocumentStatus
from ..models.domain.chunk import ChunkType
from ..repositories.document_repository import DocumentRepository
from ..repositories.chunk_repository import ChunkRepository
from .pdf import PDFParser, PDFExtractor, SectionChunker, get_pdf_cache
from .ai.embeddings import EmbeddingsService
from .ai.retrieval import RetrievalService

logger = get_logger(__name__)


class DocumentProcessingService:
    """
    Service for orchestrating document processing pipeline.

    Handles the complete workflow from PDF upload to vector storage.
    """

    def __init__(
        self,
        document_repo: DocumentRepository,
        chunk_repo: ChunkRepository,
        embedding_service: Optional[EmbeddingsService] = None,
        retrieval_service: Optional[RetrievalService] = None,
    ):
        """
        Initialize document processing service.

        Args:
            document_repo: Document repository
            chunk_repo: Chunk repository
            embedding_service: Optional embedding service
            retrieval_service: Optional retrieval service
        """
        self.document_repo = document_repo
        self.chunk_repo = chunk_repo
        self.embedding_service = embedding_service or EmbeddingsService()
        self.retrieval_service = retrieval_service
        self.pdf_cache = get_pdf_cache()

    def calculate_file_hash(self, file_path: Path) -> str:
        """
        Calculate SHA-256 hash of file.

        Args:
            file_path: Path to file

        Returns:
            Hex digest of file hash
        """
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    async def check_duplicate(self, content_hash: str) -> Optional[DocumentModel]:
        """
        Check if document with same hash already exists.

        Args:
            content_hash: SHA-256 hash of document

        Returns:
            Existing document or None
        """
        return await self.document_repo.get_by_hash(content_hash)

    async def process_document(
        self,
        file_path: Path,
        filename: str,
        use_cache: bool = True,
        chunk_strategy: str = "section",
        generate_embeddings: bool = True,
    ) -> Tuple[DocumentModel, List[ChunkModel]]:
        """
        Process a document through the complete pipeline.

        Args:
            file_path: Path to PDF file
            filename: Original filename
            use_cache: Whether to use PDF parsing cache
            chunk_strategy: Chunking strategy ("section", "hybrid", etc.)
            generate_embeddings: Whether to generate and store embeddings

        Returns:
            Tuple of (document, chunks)

        Raises:
            ProcessingError: If processing fails
        """
        logger.info(f"Starting document processing: {filename}")

        try:
            # Step 1: Calculate hash and check for duplicates
            file_size = file_path.stat().st_size
            content_hash = self.calculate_file_hash(file_path)

            existing_doc = await self.check_duplicate(content_hash)
            if existing_doc:
                logger.info(f"Document already exists: {content_hash[:16]}...")
                chunks = await self.chunk_repo.get_by_document_id(existing_doc.id)
                return existing_doc, chunks

            # Step 2: Create document record
            document = DocumentModel(
                filename=filename,
                file_path=str(file_path),
                file_size=file_size,
                content_hash=content_hash,
                status=DocumentStatus.PENDING,
            )
            document = await self.document_repo.create(document)
            await self.document_repo.commit()

            logger.info(f"Created document record: {document.id}")

            # Step 3: Update status to PROCESSING
            await self.document_repo.update_status(
                document.id,
                DocumentStatus.PROCESSING
            )
            await self.document_repo.commit()

            # Step 4: Parse PDF and extract metadata
            parser = PDFParser(str(file_path), use_cache=use_cache)
            metadata = parser.get_metadata()

            # Update document with metadata
            if metadata:
                await self.document_repo.update(
                    document.id,
                    {"doc_metadata": metadata}
                )

            logger.info(
                f"Extracted metadata: {metadata.get('pages', 0)} pages")

            # Step 5: Extract structured text
            extractor = PDFExtractor(str(file_path), use_cache=use_cache)
            structured_text = extractor.extract_structured_text()

            logger.info(f"Extracted text from {len(structured_text)} pages")

            # Step 6: Chunk the document
            chunks_data = await self._chunk_document(
                structured_text,
                file_path,
                document.id,
                chunk_strategy
            )

            logger.info(f"Created {len(chunks_data)} chunks")

            # Step 7: Generate embeddings and store in vector DB
            # TEMPORARY: Skip vector storage due to ChromaDB compatibility issues
            if False and generate_embeddings and self.retrieval_service:
                await self._generate_and_store_embeddings(
                    chunks_data,
                    document.id,
                    str(filename)
                )
                logger.info(
                    f"Generated and stored embeddings for {len(chunks_data)} chunks")
            else:
                logger.info(
                    "Skipping vector storage (disabled for compatibility)")

            # Step 8: Update document status
            await self.document_repo.update_chunk_count(document.id, len(chunks_data))
            await self.document_repo.update_status(
                document.id,
                DocumentStatus.COMPLETED
            )
            await self.document_repo.commit()

            logger.info(f"Document processing completed: {document.id}")

            return document, chunks_data

        except Exception as e:
            logger.error(
                f"Document processing failed: {str(e)}", exc_info=True)

            # Update status to FAILED if document was created
            if 'document' in locals():
                try:
                    await self.document_repo.update_status(
                        document.id,
                        DocumentStatus.FAILED,
                        error=str(e)
                    )
                    await self.document_repo.commit()
                except Exception as update_error:
                    logger.error(
                        f"Failed to update error status: {update_error}")

            raise ProcessingError(f"Failed to process document: {str(e)}")

    async def _chunk_document(
        self,
        structured_text: List[dict],
        pdf_path: Path,
        document_id: UUID,
        strategy: str = "section"
    ) -> List[ChunkModel]:
        """
        Chunk the document using specified strategy with position information.

        Args:
            structured_text: List of page text data
            pdf_path: Path to PDF file
            document_id: Document UUID
            strategy: Chunking strategy

        Returns:
            List of created chunk models with bounding box information
        """
        # Try to extract text with positions using PyMuPDF
        try:
            parser = PDFParser(pdf_path, use_cache=True)
            page_data_with_positions = parser.extract_text_with_positions()
            
            # Use PDFChunker with position information
            from .pdf.chunking import PDFChunker
            chunker = PDFChunker(use_cache=True)
            chunks_dict = chunker.chunk_with_positions(
                page_data=page_data_with_positions,
                strategy="hybrid"  # Use hybrid strategy for better results
            )
            
            logger.info(f"Created {len(chunks_dict)} chunks with position information")
            
        except Exception as e:
            # Fallback to section chunking without positions
            logger.warning(f"Failed to extract positions, falling back to section chunking: {e}")
            chunker = SectionChunker(use_cache=True)
            chunks_dict = chunker.chunk_by_sections(
                structured_text,
                str(pdf_path)
            )

        # Convert to ChunkModel instances
        chunk_models = []
        for chunk_dict in chunks_dict:
            # Extract page information
            page_numbers = chunk_dict.get("page_numbers", [])
            if not page_numbers:
                # Get page from metadata if available
                metadata = chunk_dict.get("metadata", {})
                page = metadata.get("page", 0)
                page_numbers = [page] if page else [0]
            
            start_page = min(page_numbers) if page_numbers else 0
            end_page = max(page_numbers) if page_numbers else 0

            # Extract bounding boxes from metadata
            metadata = chunk_dict.get("metadata", {})
            bounding_boxes = metadata.get("bounding_boxes", [])
            
            chunk_model = ChunkModel(
                document_id=document_id,
                content=chunk_dict.get("text", chunk_dict.get("content", "")),
                chunk_index=chunk_dict["chunk_index"],
                chunk_type=ChunkType.TEXT,
                start_page=start_page,
                end_page=end_page,
                token_count=len(chunk_dict.get("text", chunk_dict.get("content", "")).split()),
                chunk_metadata={
                    **metadata,
                    "bounding_boxes": bounding_boxes  # Store bounding boxes in metadata
                },
            )
            chunk_models.append(chunk_model)

        # Batch create chunks
        created_chunks = await self.chunk_repo.create_batch(chunk_models)
        await self.chunk_repo.commit()

        logger.info(f"Saved {len(created_chunks)} chunks to database")
        return created_chunks

    async def _generate_and_store_embeddings(
        self,
        chunks: List[ChunkModel],
        document_id: UUID,
        collection_name: str,
    ) -> None:
        """
        Generate embeddings and store in vector database.

        Args:
            chunks: List of chunk models
            document_id: Document UUID
            collection_name: Vector collection name
        """
        if not self.retrieval_service:
            logger.warning(
                "No retrieval service configured, skipping embeddings")
            return

        # Prepare texts and metadata
        texts = [chunk.content for chunk in chunks]
        metadatas = [
            {
                "chunk_id": str(chunk.id),
                "document_id": str(document_id),
                "chunk_index": chunk.chunk_index,
                "start_page": chunk.start_page,
                "end_page": chunk.end_page,
                "chunk_type": chunk.chunk_type.value,
            }
            for chunk in chunks
        ]

        # Generate embeddings - KEY FIX: Use encode_batch instead of encode
        embeddings = self.embedding_service.encode_batch(texts)

        # Prepare chunks in the format expected by RetrievalService
        chunks_with_embeddings = [
            {
                'text': text,
                'embedding': embedding.tolist() if hasattr(embedding, 'tolist') else embedding,
                'chunk_index': meta['chunk_index'],
                'start_page': meta['start_page'],
                'end_page': meta['end_page'],
                **meta
            }
            for text, embedding, meta in zip(texts, embeddings, metadatas)
        ]

        # Store in vector database - KEY FIX: RetrievalService.add_documents is not async
        result = self.retrieval_service.add_documents(
            chunks=chunks_with_embeddings,
            document_id=str(document_id)
        )

        logger.info(
            f"Added {result.get('added', 0)} chunks to vector database")

    async def delete_document(self, document_id: UUID) -> bool:
        """
        Delete document and all associated data.

        Args:
            document_id: Document UUID

        Returns:
            True if deleted, False if not found
        """
        # Get document
        document = await self.document_repo.get_by_id(document_id)
        if not document:
            return False

        # Delete from vector database if configured
        if self.retrieval_service:
            try:
                collection_name = document.filename
                await self.retrieval_service.delete_collection(collection_name)
                logger.info(f"Deleted vector collection: {collection_name}")
            except Exception as e:
                logger.warning(f"Failed to delete vector collection: {e}")

        # Delete file
        try:
            file_path = Path(document.file_path)
            if file_path.exists():
                file_path.unlink()
                logger.info(f"Deleted file: {file_path}")
        except Exception as e:
            logger.warning(f"Failed to delete file: {e}")

        # Delete from database (cascade will delete chunks)
        deleted = await self.document_repo.delete_with_chunks(document_id)
        await self.document_repo.commit()

        return deleted
