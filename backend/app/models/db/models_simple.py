"""
SQLAlchemy database models for IntelliPDF (SQLite compatible version).

This module defines the database schema using SQLAlchemy 2.0 declarative models.
All models are compatible with SQLite for development and PostgreSQL for production.
"""

from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import (
    String, Integer, Float, Boolean, Text, JSON, Enum,
    ForeignKey, Index, UniqueConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin
from ..domain.document import DocumentStatus
from ..domain.chunk import ChunkType


def generate_uuid() -> str:
    """Generate UUID as string for cross-database compatibility."""
    return str(uuid4())


class DocumentModel(Base, TimestampMixin):
    """Document database model."""

    __tablename__ = "documents"

    # Primary Key (String for SQLite compatibility)
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=generate_uuid,
        comment="Document unique identifier"
    )

    # File Information
    filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Original filename"
    )
    file_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        unique=True,
        comment="File storage path"
    )
    file_size: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="File size in bytes"
    )
    content_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        unique=True,
        index=True,
        comment="SHA-256 hash of file content"
    )

    # Processing Status
    status: Mapped[DocumentStatus] = mapped_column(
        Enum(DocumentStatus, native_enum=False),
        nullable=False,
        default=DocumentStatus.PENDING,
        index=True,
        comment="Document processing status"
    )
    processing_started_at: Mapped[Optional[datetime]] = mapped_column(
        nullable=True,
        comment="Processing start timestamp"
    )
    processing_completed_at: Mapped[Optional[datetime]] = mapped_column(
        nullable=True,
        comment="Processing completion timestamp"
    )
    processing_error: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Error message if processing failed"
    )

    # Metadata (stored as JSON) - using different column name to avoid SQLAlchemy reserved word
    doc_metadata: Mapped[Optional[dict]] = mapped_column(
        "metadata",
        JSON,
        nullable=True,
        comment="Document metadata (title, author, etc.)"
    )

    # Statistics
    chunk_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Number of chunks"
    )

    # Relationships
    chunks: Mapped[list["ChunkModel"]] = relationship(
        "ChunkModel",
        back_populates="document",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    # Indexes
    __table_args__ = (
        Index("idx_documents_status_created", "status", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<DocumentModel(id={self.id}, filename={self.filename}, status={self.status})>"


class ChunkModel(Base, TimestampMixin):
    """Chunk database model."""

    __tablename__ = "chunks"

    # Primary Key
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=generate_uuid,
        comment="Chunk unique identifier"
    )

    # Foreign Key
    document_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Parent document ID"
    )

    # Content
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Chunk content text"
    )

    # Position Information
    chunk_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Chunk index in document (0-based)"
    )
    start_page: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Starting page number"
    )
    end_page: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Ending page number"
    )

    # Type and Metrics
    chunk_type: Mapped[ChunkType] = mapped_column(
        Enum(ChunkType, native_enum=False),
        nullable=False,
        default=ChunkType.TEXT,  # Fixed: use TEXT as default
        index=True,
        comment="Type of chunk"
    )
    token_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Estimated token count"
    )

    # Vector Database Reference
    vector_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        unique=True,
        index=True,
        comment="Vector database ID"
    )

    # Additional Metadata (stored as JSON)
    chunk_metadata: Mapped[Optional[dict]] = mapped_column(
        "metadata",
        JSON,
        nullable=True,
        comment="Additional metadata"
    )

    # Relationships
    document: Mapped["DocumentModel"] = relationship(
        "DocumentModel",
        back_populates="chunks",
        lazy="selectin"
    )

    # Indexes
    __table_args__ = (
        Index("idx_chunks_document_index", "document_id", "chunk_index"),
        Index("idx_chunks_pages", "document_id", "start_page", "end_page"),
    )

    def __repr__(self) -> str:
        return f"<ChunkModel(id={self.id}, document_id={self.document_id}, index={self.chunk_index})>"


class UserModel(Base, TimestampMixin):
    """User database model for authentication."""

    __tablename__ = "users"

    # Primary Key
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=generate_uuid,
        comment="User unique identifier"
    )

    # Authentication
    username: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True,
        index=True,
        comment="Unique username for login"
    )
    email: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
        comment="User email address"
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Bcrypt hashed password"
    )

    # Profile
    full_name: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="User's full name"
    )

    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
        comment="Whether user account is active"
    )
    is_superuser: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Whether user has admin privileges"
    )

    # API Configuration (encrypted)
    gemini_api_key: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="User's encrypted Gemini API key"
    )

    # Activity Tracking
    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        nullable=True,
        comment="Last login timestamp"
    )

    # Indexes
    __table_args__ = (
        Index("idx_users_active", "is_active"),
        UniqueConstraint("username", name="uq_users_username"),
        UniqueConstraint("email", name="uq_users_email"),
    )

    def __repr__(self) -> str:
        return f"<UserModel(id={self.id}, username={self.username}, email={self.email})>"


class BookmarkModel(Base, TimestampMixin):
    """Bookmark database model with AI-generated summaries."""

    __tablename__ = "bookmarks"

    # Primary Key
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=generate_uuid,
        comment="Bookmark unique identifier"
    )

    # Foreign Keys
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Owner user ID"
    )
    document_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Associated document ID"
    )
    chunk_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("chunks.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Associated chunk ID"
    )

    # Selected Text & Position
    selected_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="User-selected text content"
    )
    page_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
        comment="Page number where bookmark is located"
    )

    # Position (Bounding Box)
    position_x: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="X coordinate of selection"
    )
    position_y: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Y coordinate of selection"
    )
    position_width: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Width of selection"
    )
    position_height: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Height of selection"
    )

    # AI-Generated Content
    ai_summary: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="AI-generated bookmark summary"
    )

    # User Content
    title: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="Bookmark title"
    )
    user_notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="User's additional notes"
    )

    # Metadata
    conversation_context: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="Associated conversation history"
    )
    tags: Mapped[Optional[list]] = mapped_column(
        JSON,
        nullable=True,
        default=[],
        comment="User-defined tags"
    )
    color: Mapped[str] = mapped_column(
        String(7),
        nullable=False,
        default="#FCD34D",
        comment="Highlight color (hex)"
    )

    # Indexes
    __table_args__ = (
        Index("idx_bookmarks_user_document", "user_id", "document_id"),
        Index("idx_bookmarks_page", "document_id", "page_number"),
    )

    def __repr__(self) -> str:
        return f"<BookmarkModel(id={self.id}, user_id={self.user_id}, document_id={self.document_id}, page={self.page_number})>"


class TagModel(Base, TimestampMixin):
    """Tag model for organizing annotations and bookmarks."""

    __tablename__ = "tags"

    # Primary Key
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=generate_uuid,
        comment="Tag unique identifier"
    )

    # Foreign Key
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Owner user ID"
    )

    # Tag Properties
    name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Tag name"
    )
    color: Mapped[str] = mapped_column(
        String(7),
        nullable=False,
        default="#3B82F6",
        comment="Tag color (hex)"
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Tag description"
    )

    # Indexes
    __table_args__ = (
        Index("idx_tags_user", "user_id"),
        UniqueConstraint("user_id", "name", name="uq_tags_user_name"),
    )

    def __repr__(self) -> str:
        return f"<TagModel(id={self.id}, name={self.name})>"


class AIQuestionModel(Base, TimestampMixin):
    """AI Question model for tracking context-based AI inquiries."""

    __tablename__ = "ai_questions"

    # Primary Key
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=generate_uuid,
        comment="Question unique identifier"
    )

    # Foreign Keys
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="User ID"
    )
    document_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Associated document ID"
    )
    chunk_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("chunks.id", ondelete="SET NULL"),
        nullable=True,
        comment="Context chunk ID"
    )

    # Question & Context
    selected_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Selected text being questioned"
    )
    context_text: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Surrounding context from chunk"
    )
    user_question: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="User's question about the selected text"
    )
    ai_answer: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="AI-generated answer"
    )

    # Position
    page_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
        comment="Page number"
    )
    position_x: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="X coordinate"
    )
    position_y: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Y coordinate"
    )

    # Metadata
    model_used: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="gemini-1.5-flash",
        comment="AI model used"
    )
    response_metadata: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="Additional response metadata"
    )

    # Indexes
    __table_args__ = (
        Index("idx_ai_questions_user_document", "user_id", "document_id"),
        Index("idx_ai_questions_page", "document_id", "page_number"),
    )

    def __repr__(self) -> str:
        return f"<AIQuestionModel(id={self.id}, page={self.page_number})>"


# Simplified models - remove complex features not needed initially
# We can add KnowledgeNode, KnowledgeEdge, ChatSession, ChatMessage later


class AnnotationModel(Base, TimestampMixin):
    """
    PDF Annotation database model.
    Stores all types of annotations: text markup, shapes, ink, notes, etc.
    """

    __tablename__ = "annotations"

    # Primary Key
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=generate_uuid,
        comment="Annotation unique identifier"
    )

    # Foreign Keys
    document_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Related document ID"
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        nullable=False,
        index=True,
        comment="User who created the annotation"
    )

    # Annotation Type
    annotation_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Type: text-markup, shape, ink, textbox, note, stamp, signature"
    )

    # Page Information
    page_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
        comment="Page number (1-indexed)"
    )

    # Complete Annotation Data (JSON)
    # Stores textAnchor, pdfCoordinates, style, and other type-specific data
    data: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        comment="Complete annotation data (textAnchor, pdfCoordinates, style, etc.)"
    )

    # Quick Access Fields (denormalized for performance)
    content: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Text content (for text-based annotations)"
    )
    color: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="Annotation color (hex)"
    )

    # Tags (for filtering)
    tags: Mapped[list] = mapped_column(
        JSON,
        nullable=False,
        default=list,
        comment="User-defined tags"
    )

    # Metadata
    user_name: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Username for display"
    )

    # Relationships
    document: Mapped["DocumentModel"] = relationship(
        "DocumentModel",
        backref="annotations"
    )

    # Indexes for common queries
    __table_args__ = (
        Index("idx_annotations_document_page", "document_id", "page_number"),
        Index("idx_annotations_user", "user_id", "created_at"),
        Index("idx_annotations_type", "annotation_type", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<AnnotationModel(id={self.id}, type={self.annotation_type}, page={self.page_number})>"


class AnnotationReplyModel(Base, TimestampMixin):
    """
    Annotation reply/comment model.
    Supports threaded discussions on annotations.
    """

    __tablename__ = "annotation_replies"

    # Primary Key
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=generate_uuid,
        comment="Reply unique identifier"
    )

    # Foreign Keys
    annotation_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("annotations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Parent annotation ID"
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        nullable=False,
        index=True,
        comment="User who created the reply"
    )
    parent_reply_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("annotation_replies.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="Parent reply ID (for threading)"
    )

    # Content
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Reply text content"
    )

    # Metadata
    user_name: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Username for display"
    )

    # Relationships
    annotation: Mapped["AnnotationModel"] = relationship(
        "AnnotationModel",
        backref="replies"
    )
    parent_reply: Mapped[Optional["AnnotationReplyModel"]] = relationship(
        "AnnotationReplyModel",
        remote_side=[id],
        backref="child_replies"
    )

    # Indexes
    __table_args__ = (
        Index("idx_replies_annotation", "annotation_id", "created_at"),
        Index("idx_replies_user", "user_id", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<AnnotationReplyModel(id={self.id}, annotation_id={self.annotation_id})>"
