import asyncio
import os

from app.core.config import get_settings
from app.infrastructure.database.session import get_session_factory
from app.repositories.document_repository import DocumentRepository
from app.repositories.chunk_repository import ChunkRepository
from app.services.document_processing_service import DocumentProcessingService
from app.services.ai.embeddings import EmbeddingsService
from app.services.ai.retrieval import RetrievalService


async def main():
    settings = get_settings()
    from pathlib import Path
    # Uploaded files are stored under the backend directory
    file_path = Path('D:/IntelliPDF/backend/data/uploads/Linux教程.pdf')
    session_factory = get_session_factory()
    db = session_factory()
    try:
        doc_repo = DocumentRepository(db)
        chunk_repo = ChunkRepository(db)
        embedding_service = EmbeddingsService()
        retrieval_service = RetrievalService()
        svc = DocumentProcessingService(
            document_repo=doc_repo,
            chunk_repo=chunk_repo,
            embedding_service=embedding_service,
            retrieval_service=retrieval_service,
        )
        document, chunks = await svc.process_document(
            file_path=file_path,
            filename='Linux教程.pdf',
            use_cache=False,
            chunk_strategy='section',
            generate_embeddings=True,
        )
        print('processed', document.id, 'chunks', len(chunks))
    finally:
        await db.close()


if __name__ == '__main__':
    asyncio.run(main())
