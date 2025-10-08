"""Database models package"""

from .base import Base
# Use simplified SQLite-compatible models
from .models_simple import (
    DocumentModel,
    ChunkModel,
    UserModel,
    BookmarkModel,
    AnnotationModel,
    TagModel,
    AIQuestionModel,
)

__all__ = [
    "Base",
    "DocumentModel",
    "ChunkModel",
    "UserModel",
    "BookmarkModel",
    "AnnotationModel",
    "TagModel",
    "AIQuestionModel",
]
