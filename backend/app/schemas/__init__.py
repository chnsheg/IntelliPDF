"""
Pydantic schemas for API request and response models.

This package contains all schema definitions for API data validation
and serialization.
"""

from .document import (
    DocumentBase,
    DocumentCreate,
    DocumentUpdate,
    DocumentInDB,
    DocumentResponse,
    DocumentListResponse,
    DocumentStatistics,
)
from .chunk import (
    ChunkBase,
    ChunkCreate,
    ChunkInDB,
    ChunkResponse,
    ChunkListResponse,
)
from .chat import (
    ChatRequest,
    ChatResponse,
    Message,
)
from .summary import (
    SummaryRequest,
    SummaryResponse,
    KeywordsRequest,
    KeywordsResponse,
)
from .common import (
    StatusResponse,
    ErrorResponse,
    PaginationParams,
)
from .bookmark import (
    BookmarkPosition,
    BookmarkBase,
    BookmarkCreate,
    BookmarkUpdate,
    BookmarkResponse,
    BookmarkListResponse,
    BookmarkSearchRequest,
    BookmarkGenerateRequest,
    BookmarkStatistics,
)

__all__ = [
    # Document schemas
    "DocumentBase",
    "DocumentCreate",
    "DocumentUpdate",
    "DocumentInDB",
    "DocumentResponse",
    "DocumentListResponse",
    "DocumentStatistics",
    # Chunk schemas
    "ChunkBase",
    "ChunkCreate",
    "ChunkInDB",
    "ChunkResponse",
    "ChunkListResponse",
    # Chat schemas
    "ChatRequest",
    "ChatResponse",
    "Message",
    # Summary schemas
    "SummaryRequest",
    "SummaryResponse",
    "KeywordsRequest",
    "KeywordsResponse",
    # Common schemas
    "StatusResponse",
    "ErrorResponse",
    "PaginationParams",
    # Bookmark schemas
    "BookmarkPosition",
    "BookmarkBase",
    "BookmarkCreate",
    "BookmarkUpdate",
    "BookmarkResponse",
    "BookmarkListResponse",
    "BookmarkSearchRequest",
    "BookmarkGenerateRequest",
    "BookmarkStatistics",
]
