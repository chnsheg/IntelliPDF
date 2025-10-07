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


# Simplified models - remove complex features not needed initially
# We can add KnowledgeNode, KnowledgeEdge, Bookmark, ChatSession, ChatMessage later
