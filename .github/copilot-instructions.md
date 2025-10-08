# IntelliPDF AI Agent Instructions

## Project Overview
IntelliPDF transforms static PDFs into interactive AI-powered knowledge graphs using AI. **Monorepo structure**: `backend/` (FastAPI + Python 3.11) and `frontend/` (React 18 + TypeScript + Vite).

**Architecture**: Domain-Driven Design (DDD) with strict separation: domain logic in `services/`, data access in `repositories/`, persistence in `models/db/`.

**Key Tech**: FastAPI, SQLAlchemy 2.0 (async), ChromaDB (vectors), Gemini API (LLM), PyMuPDF (parsing), React 18, TailwindCSS.

## Critical Architecture Patterns

### 1. Two-Model System (NEVER mix these)
```python
# Domain Models (models/domain/) - Business logic, validation, no SQLAlchemy
from ..models.domain.document import Document, DocumentStatus

# Database Models (models/db/models_simple.py) - ORM persistence only
from ..models.db import DocumentModel, ChunkModel  # ALWAYS import via __init__.py
```
**Why**: Decouples business rules from database schema. Services work with domain models, repositories translate to/from DB models.
**Critical**: SQLite backend uses String(36) for UUIDs. Convert `UUID` objects to strings in queries: `str(id)` before database lookups.

### 2. Repository Pattern (Generic Typed Base)
```python
class DocumentRepository(BaseRepository[DocumentModel]):
    def __init__(self, session: AsyncSession):
        super().__init__(DocumentModel, session)
    # All CRUD methods inherited: create, get_by_id, get_multi, update, delete
```
**Pattern**: Every entity has a repository extending `BaseRepository[ModelType]`. NO direct SQLAlchemy queries in services.

### 3. Dependency Injection (Per-Request Construction)
```python
# In endpoints/documents.py
async def get_document_service(db: AsyncSession = Depends(get_db)) -> DocumentProcessingService:
    """Dependency function constructing service with all dependencies"""
    return DocumentProcessingService(
        document_repo=DocumentRepository(db),
        chunk_repo=ChunkRepository(db),
        embedding_service=EmbeddingsService(),
        retrieval_service=RetrievalService(),
    )

@router.post("/upload")
async def upload(file: UploadFile, service: DocumentProcessingService = Depends(get_document_service)):
    return await service.process_document(file)
```
**Critical**: 
- Services are stateless, constructed per-request via `Depends()`
- Database session lifecycle managed by FastAPI dependencies
- Create `get_*_service()` functions in endpoint files, NOT in services themselves

### 4. Configuration (Singleton Pattern)
```python
from ..core.config import get_settings
settings = get_settings()  # Cached singleton, reads from .env
# NEVER hardcode: API keys, URLs, paths, timeouts
```

## Key Workflows & Entry Points

### PDF Processing Pipeline
**Entry**: `services/document_processing_service.py::process_document()`
1. **Cache Check**: `services/pdf/cache.py` - SHA-256 hash lookup (skip re-parsing identical files)
2. **Parse**: `services/pdf/parser.py` - PyMuPDF extraction
3. **Chunk**: `services/pdf/chunking.py::SectionChunker` - Structure-aware splitting
4. **Embed**: `services/ai/embeddings.py` - Gemini text-embedding model
5. **Store**: ChromaDB (vectors) + SQLite (metadata)

**Cache Location**: `data/pdf_cache/{hash}/` with metadata.json + chunks.json

### AI/LLM Integration (Custom Gemini Client)
```python
# infrastructure/ai/gemini_client.py uses v1beta API format
# URL pattern: {base_url}/v1beta/models/{model}:generateContent?key={api_key}
from ..infrastructure.ai.gemini_client import GeminiClient
client = GeminiClient()
response = await client.generate_content(prompt, system_instruction="...")
```
**Why Custom**: Standard SDKs don't support proxy endpoints. Our client handles `?key=` auth and streaming.

### Database Migrations (Alembic)
```powershell
# Always run before starting server
alembic upgrade head
# Create new migration after model changes
alembic revision --autogenerate -m "description"
```

## Development Commands (Windows/PowerShell)

### Start Backend (Automated)
```powershell
cd backend
.\start.bat  # Checks venv → .env → migrations → uvicorn
```

### Start Frontend (React + Vite)
```powershell
cd frontend
npm run dev  # Runs on http://localhost:5173
```

### Run Integration Tests
```powershell
# Root-level test files use live services (no mocks)
python test_api_complete.py       # Full endpoint suite
python test_gemini_simple.py      # AI service tests
python test_pdf_processing.py     # PDF pipeline
```

### Clean Cache/Restart
```powershell
cd backend
# Kill all Python processes
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force
# Clean pycache
Get-ChildItem -Path . -Filter "__pycache__" -Recurse | Remove-Item -Recurse -Force
.\venv\Scripts\Activate.ps1; python main.py
```

## Project-Specific Conventions

### Import Style (Strict Rules)
```python
# ✅ Correct - Relative imports within app/, absolute from main.py only
# Inside app/ modules:
from ..core.config import get_settings
from ..models.db import DocumentModel  # MUST import via __init__.py
from ..infrastructure.ai.gemini_client import GeminiClient

# From root (main.py, alembic/env.py):
from app.core.config import get_settings
from app.models.db import DocumentModel

# ❌ Wrong - Direct file imports bypass __init__.py exports
from ..models.db.models_simple import DocumentModel  # NEVER do this
from app.models.db.models_simple import DocumentModel  # NEVER do this
```
**Why**: `__init__.py` controls public API and switches between SQLite/PostgreSQL models.

### Async Everything
```python
# ALL database operations are async
async def example(db: AsyncSession):
    async with db.begin():  # Explicit transaction
        doc = await repo.get_by_id(doc_id)
        await repo.update(doc)
        await db.commit()  # Explicit commit
```

### Error Handling (Custom Hierarchy)
```python
from ..core.exceptions import PDFProcessingError, AIServiceError, DatabaseError
# Raise specific exceptions, FastAPI middleware converts to HTTP responses
raise PDFProcessingError(
    message="Failed to parse PDF",
    error_code="PDF_PARSE_001",
    details={"filename": file.name, "size": file.size}
)
```

### Logging (Structured with loguru)
```python
from ..core.logging import get_logger
logger = get_logger(__name__)
# Use f-strings with context
logger.info(f"Processing document {doc_id}", extra={"user_id": user.id, "size": file_size})
```

## Adding New Features (Step-by-Step)

### New API Endpoint
1. **Schema**: Define in `schemas/` (Pydantic request/response models)
2. **Service**: Add business logic in `services/` (use existing repositories)
3. **Dependency**: Create `get_*_service()` function in endpoint file
4. **Endpoint**: Add route in `api/v1/endpoints/`, use `Depends(get_*_service)`
5. **Router**: Include in `api/v1/router.py`
6. **Test**: Add to root-level test file

### New Database Model
1. **Domain**: Create in `models/domain/` (business entity)
2. **DB Model**: Add SQLAlchemy model in `models/db/models_simple.py`
3. **Export**: Add to `models/db/__init__.py`
4. **Repository**: Extend `BaseRepository[YourModel]` in `repositories/`
5. **Migration**: Run `alembic revision --autogenerate -m "add_your_model"`
6. **Apply**: `alembic upgrade head`

## API Structure & Access

- **Base URL**: http://localhost:8000
- **API Prefix**: `/api/v1` (all endpoints under this)
- **Health**: `/health` (root level, NOT under /api/v1)
- **Docs**: http://localhost:8000/api/docs (Swagger UI)
- **CORS**: Enabled for `http://localhost:5173` (frontend dev server)

## Frontend Integration (React + TypeScript)

### API Client Pattern
```typescript
// frontend/src/services/api.ts - Axios with interceptors
class ApiService {
    private client: AxiosInstance;
    constructor() {
        this.client = axios.create({
            baseURL: '/api/v1',  // Proxied in vite.config.ts
            timeout: 60000,
        });
    }
}
```

### State Management (Zustand)
- Stores in `frontend/src/stores/` 
- React Query for server state (`@tanstack/react-query`)
- Local state for UI (Zustand slices)

## Technology Stack & Key Dependencies

**Backend**:
- FastAPI (async framework)
- SQLAlchemy 2.0 (async ORM)
- Alembic (migrations)
- ChromaDB (vector storage)
- Gemini API (LLM + embeddings)
- PyMuPDF/pdfplumber (PDF parsing)
- Loguru (logging)
- Pydantic (validation)

**Frontend**:
- React 18 + TypeScript
- Vite (build tool)
- TailwindCSS (styling)
- React Router (routing)
- Zustand (state)
- React Query (server state)
- PDF.js (rendering)
- ReactFlow (knowledge graph)

## Current Status & Known Limitations

✅ **Production-Ready**: Core API, PDF upload/processing, AI chat, caching, database
🚧 **Beta**: Knowledge graph extraction, advanced chunking strategies
⚠️ **Known Issues**: 
- Large PDFs (>50MB) may timeout on first parse
- Gemini rate limits not yet implemented
- No authentication (planned)
- SQLite UUIDs stored as String(36) - always convert UUID objects to strings in queries

**Progress Tracking**: See `PROJECT_TODO.md` for roadmap and `ARCHITECTURE.md` for deep-dive design docs.
