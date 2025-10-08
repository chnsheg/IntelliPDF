import asyncio
from pathlib import Path
from app.core.config import get_settings
from app.infrastructure.database.session import get_session_factory
from app.repositories.chunk_repository import ChunkRepository
from app.repositories.document_repository import DocumentRepository
from app.services.ai.retrieval import RetrievalService


def to_chunk_dict(chunk):
    return {
        'text': chunk.content,
        'chunk_index': chunk.chunk_index,
        'start_page': chunk.start_page,
        'end_page': chunk.end_page,
        'char_count': len(chunk.content) if chunk.content else 0,
    }


async def main(document_id: str):
    session_factory = get_session_factory()
    async with session_factory() as session:
        doc_repo = DocumentRepository(session)
        chunk_repo = ChunkRepository(session)
        doc = await doc_repo.get_by_id(document_id)
        if not doc:
            print('Document not found', document_id)
            return
        chunks = await chunk_repo.get_by_document_id(document_id, skip=0, limit=5000)
        print('fetched', len(chunks), 'chunks from DB')
        if not chunks:
            print('No chunks to add')
            return
        retrieval = RetrievalService()
        # Use chunk.id (UUID) as stable unique ID for Chroma
        chunk_dicts = [dict(to_chunk_dict(c), id=str(
            c.id), chunk_db_id=str(c.id)) for c in chunks]
        # Clear existing collection to avoid duplicate ID errors on re-import
        try:
            retrieval.clear_collection()
        except Exception:
            pass

        # The retrieval.add_documents expects chunks list with 'text' and optional 'embedding'
        # We'll map our dicts to the expected shape inside the retrieval service.
        res = retrieval.add_documents(
            chunks=chunk_dicts, document_id=str(document_id), batch_size=200)
        print('add result', res)


if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print('Usage: add_chunks_to_chroma.py <document_id>')
        sys.exit(1)
    asyncio.run(main(sys.argv[1]))
