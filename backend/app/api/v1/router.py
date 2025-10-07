"""
API v1 main router.

This module aggregates all v1 endpoint routers.
"""

from fastapi import APIRouter

from .endpoints import documents, health, test, documents_enhanced, knowledge_graph

api_router = APIRouter()

# Test endpoints
api_router.include_router(test.router, prefix="/test", tags=["test"])

# Document management endpoints
api_router.include_router(
    documents.router,
    prefix="/documents",
    tags=["documents"]
)

# Enhanced document endpoints (batch operations, advanced search)
api_router.include_router(
    documents_enhanced.router,
    prefix="/documents-enhanced",
    tags=["documents-enhanced"]
)

# Knowledge graph endpoints
api_router.include_router(
    knowledge_graph.router,
    prefix="/knowledge-graph",
    tags=["knowledge-graph"]
)

# Additional routers will be added as they're implemented
# api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
# api_router.include_router(bookmarks.router, prefix="/bookmarks", tags=["bookmarks"])
