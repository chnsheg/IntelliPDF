"""
SQLAlchemy database models for IntelliPDF.

This module defines the database schema using SQLAlchemy 2.0 declarative models.
All models use type hints and support async operations.
"""

from .base import Base, TimestampMixin
from ..domain.knowledge import NodeType, EdgeType
from ..domain.chunk import ChunkType
from ..domain.document import DocumentStatus
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import (
    String, Integer, Float, Boolean, Text, JSON, Enum,
    ForeignKey, Index, UniqueConstraint, CheckConstraint,
    LargeBinary, ARRAY
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

# Helper function to convert UUID to string for SQLite compatibility


def uuid_str():
    """Generate UUID as string for cross-database compatibility."""
    return str(uuid4())


class DocumentModel(Base, TimestampMixin):
    """
    Document database model.

    Stores PDF document information and processing status.
    """

    __tablename__ = "documents"

    # Primary Key (String for SQLite compatibility)
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=uuid_str,
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
        Enum(DocumentStatus, name="document_status"),
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

    # Metadata (stored as JSON) - renamed to avoid SQLAlchemy reserved word
    doc_metadata: Mapped[Optional[dict]] = mapped_column(
        "metadata",  # Column name in database
        JSON,
        nullable=True,
        comment="Document metadata (title, author, etc.)"
    )

    # Statistics
    chunk_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Number of semantic chunks"
    )

    # Relationships
    chunks: Mapped[list["ChunkModel"]] = relationship(
        "ChunkModel",
        back_populates="document",
        cascade="all, delete-orphan"
    )
    knowledge_nodes: Mapped[list["KnowledgeNodeModel"]] = relationship(
        "KnowledgeNodeModel",
        back_populates="document",
        cascade="all, delete-orphan"
    )
    bookmarks: Mapped[list["BookmarkModel"]] = relationship(
        "BookmarkModel",
        back_populates="document",
        cascade="all, delete-orphan"
    )
    chat_sessions: Mapped[list["ChatSessionModel"]] = relationship(
        "ChatSessionModel",
        back_populates="document",
        cascade="all, delete-orphan"
    )

    # Table constraints
    __table_args__ = (
        CheckConstraint("file_size > 0", name="positive_file_size"),
        CheckConstraint("chunk_count >= 0", name="non_negative_chunk_count"),
        Index("idx_documents_status_created", "status", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Document(id={self.id}, filename={self.filename}, status={self.status})>"


class ChunkModel(Base, TimestampMixin):
    """
    Semantic chunk database model.

    Stores extracted content chunks with embeddings and metadata.
    """

    __tablename__ = "chunks"

    # Primary Key
    chunk_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        comment="Chunk unique identifier"
    )

    # Foreign Key
    document_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Parent document ID"
    )

    # Content
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Chunk text content"
    )
    chunk_type: Mapped[ChunkType] = mapped_column(
        Enum(ChunkType, name="chunk_type"),
        nullable=False,
        index=True,
        comment="Type of content"
    )

    # Semantic Information
    semantic_topic: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="AI-extracted topic"
    )
    importance_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.5,
        comment="Importance score (0-1)"
    )

    # Vector Embedding (stored in separate vector DB, ID reference here)
    vector_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        comment="Vector database ID reference"
    )

    # Structure Information
    structural_path: Mapped[list[str]] = mapped_column(
        ARRAY(String),
        nullable=False,
        default=list,
        comment="Document structure path"
    )
    sequence_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Sequence order in document"
    )

    # Location in PDF
    page_number: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Page number"
    )
    bounding_box: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="Bounding box coordinates"
    )

    # Statistics
    char_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Character count"
    )
    word_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Word count"
    )
    language: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True,
        comment="Language code"
    )

    # Additional Metadata
    chunk_metadata: Mapped[dict] = mapped_column(
        "metadata",
        JSON,
        nullable=False,
        default=dict,
        comment="Additional metadata"
    )

    # Relationships
    document: Mapped["DocumentModel"] = relationship(
        "DocumentModel",
        back_populates="chunks"
    )

    # Table constraints
    __table_args__ = (
        CheckConstraint(
            "importance_score >= 0 AND importance_score <= 1", name="valid_importance_score"),
        CheckConstraint("sequence_number >= 0", name="non_negative_sequence"),
        CheckConstraint("char_count >= 0", name="non_negative_char_count"),
        CheckConstraint("word_count >= 0", name="non_negative_word_count"),
        Index("idx_chunks_document_sequence",
              "document_id", "sequence_number"),
        Index("idx_chunks_type_importance", "chunk_type", "importance_score"),
    )

    def __repr__(self) -> str:
        return f"<Chunk(id={self.chunk_id}, document_id={self.document_id}, type={self.chunk_type})>"


class KnowledgeNodeModel(Base, TimestampMixin):
    """
    Knowledge graph node database model.

    Stores knowledge concepts extracted from documents.
    """

    __tablename__ = "knowledge_nodes"

    # Primary Key
    node_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        comment="Node unique identifier"
    )

    # Foreign Key
    document_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Source document ID"
    )

    # Node Information
    label: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        index=True,
        comment="Node label (concept name)"
    )
    node_type: Mapped[NodeType] = mapped_column(
        Enum(NodeType, name="node_type"),
        nullable=False,
        index=True,
        comment="Type of knowledge node"
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Detailed description"
    )

    # Scoring
    importance_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.5,
        comment="Importance score (0-1)"
    )
    difficulty_level: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        comment="Difficulty level (1-5)"
    )

    # Associated Data
    chunk_ids: Mapped[list[str]] = mapped_column(
        ARRAY(String),
        nullable=False,
        default=list,
        comment="Associated chunk IDs"
    )
    keywords: Mapped[list[str]] = mapped_column(
        ARRAY(String),
        nullable=False,
        default=list,
        comment="Associated keywords"
    )

    # Metadata
    node_metadata: Mapped[dict] = mapped_column(
        "metadata",
        JSON,
        nullable=False,
        default=dict,
        comment="Additional metadata"
    )

    # Relationships
    document: Mapped["DocumentModel"] = relationship(
        "DocumentModel",
        back_populates="knowledge_nodes"
    )
    outgoing_edges: Mapped[list["KnowledgeEdgeModel"]] = relationship(
        "KnowledgeEdgeModel",
        foreign_keys="KnowledgeEdgeModel.source_node_id",
        back_populates="source_node",
        cascade="all, delete-orphan"
    )
    incoming_edges: Mapped[list["KnowledgeEdgeModel"]] = relationship(
        "KnowledgeEdgeModel",
        foreign_keys="KnowledgeEdgeModel.target_node_id",
        back_populates="target_node",
        cascade="all, delete-orphan"
    )

    # Table constraints
    __table_args__ = (
        CheckConstraint(
            "importance_score >= 0 AND importance_score <= 1", name="valid_node_importance"),
        CheckConstraint(
            "difficulty_level >= 1 AND difficulty_level <= 5", name="valid_difficulty"),
        Index("idx_nodes_document_type", "document_id", "node_type"),
    )

    def __repr__(self) -> str:
        return f"<KnowledgeNode(id={self.node_id}, label={self.label}, type={self.node_type})>"


class KnowledgeEdgeModel(Base, TimestampMixin):
    """
    Knowledge graph edge database model.

    Stores relationships between knowledge nodes.
    """

    __tablename__ = "knowledge_edges"

    # Primary Key
    edge_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        comment="Edge unique identifier"
    )

    # Foreign Keys
    source_node_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("knowledge_nodes.node_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Source node ID"
    )
    target_node_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("knowledge_nodes.node_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Target node ID"
    )

    # Edge Information
    edge_type: Mapped[EdgeType] = mapped_column(
        Enum(EdgeType, name="edge_type"),
        nullable=False,
        index=True,
        comment="Type of relationship"
    )
    weight: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=1.0,
        comment="Edge weight (0-1)"
    )
    description: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Relationship description"
    )

    # Metadata
    edge_metadata: Mapped[dict] = mapped_column(
        "metadata",
        JSON,
        nullable=False,
        default=dict,
        comment="Additional metadata"
    )

    # Relationships
    source_node: Mapped["KnowledgeNodeModel"] = relationship(
        "KnowledgeNodeModel",
        foreign_keys=[source_node_id],
        back_populates="outgoing_edges"
    )
    target_node: Mapped["KnowledgeNodeModel"] = relationship(
        "KnowledgeNodeModel",
        foreign_keys=[target_node_id],
        back_populates="incoming_edges"
    )

    # Table constraints
    __table_args__ = (
        CheckConstraint("weight >= 0 AND weight <= 1",
                        name="valid_edge_weight"),
        CheckConstraint("source_node_id != target_node_id",
                        name="no_self_loops"),
        UniqueConstraint("source_node_id", "target_node_id",
                         "edge_type", name="unique_edge"),
        Index("idx_edges_source_type", "source_node_id", "edge_type"),
        Index("idx_edges_target_type", "target_node_id", "edge_type"),
    )

    def __repr__(self) -> str:
        return f"<KnowledgeEdge(id={self.edge_id}, type={self.edge_type})>"


class BookmarkModel(Base, TimestampMixin):
    """
    Bookmark database model.

    Stores user bookmarks for document content.
    """

    __tablename__ = "bookmarks"

    # Primary Key
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        comment="Bookmark unique identifier"
    )

    # Foreign Key
    document_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Document ID"
    )

    # Bookmark Information
    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Bookmark title"
    )
    content: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Bookmarked content excerpt"
    )
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="User notes"
    )

    # Location
    page_number: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Page number"
    )
    chunk_ids: Mapped[list[str]] = mapped_column(
        ARRAY(String),
        nullable=False,
        default=list,
        comment="Associated chunk IDs"
    )

    # Metadata
    bookmark_metadata: Mapped[dict] = mapped_column(
        "metadata",
        JSON,
        nullable=False,
        default=dict,
        comment="Additional metadata"
    )

    # Relationships
    document: Mapped["DocumentModel"] = relationship(
        "DocumentModel",
        back_populates="bookmarks"
    )

    # Table constraints
    __table_args__ = (
        Index("idx_bookmarks_document_created", "document_id", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Bookmark(id={self.id}, title={self.title})>"


class ChatSessionModel(Base, TimestampMixin):
    """
    Chat session database model.

    Stores chat sessions for document interactions.
    """

    __tablename__ = "chat_sessions"

    # Primary Key
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        comment="Session unique identifier"
    )

    # Foreign Key
    document_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Document ID"
    )

    # Session Information
    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Session title"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Session active status"
    )
    message_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Number of messages"
    )

    # Metadata
    session_metadata: Mapped[dict] = mapped_column(
        "metadata",
        JSON,
        nullable=False,
        default=dict,
        comment="Session metadata"
    )

    # Relationships
    document: Mapped["DocumentModel"] = relationship(
        "DocumentModel",
        back_populates="chat_sessions"
    )
    messages: Mapped[list["ChatMessageModel"]] = relationship(
        "ChatMessageModel",
        back_populates="session",
        cascade="all, delete-orphan"
    )

    # Table constraints
    __table_args__ = (
        CheckConstraint("message_count >= 0",
                        name="non_negative_message_count"),
        Index("idx_sessions_document_active", "document_id", "is_active"),
    )

    def __repr__(self) -> str:
        return f"<ChatSession(id={self.id}, title={self.title})>"


class ChatMessageModel(Base, TimestampMixin):
    """
    Chat message database model.

    Stores individual chat messages in sessions.
    """

    __tablename__ = "chat_messages"

    # Primary Key
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        comment="Message unique identifier"
    )

    # Foreign Key
    session_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("chat_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Chat session ID"
    )

    # Message Information
    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Message role (user/assistant/system)"
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Message content"
    )
    sequence_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Message sequence in session"
    )

    # Context
    context_chunks: Mapped[list[str]] = mapped_column(
        ARRAY(String),
        nullable=False,
        default=list,
        comment="Relevant chunk IDs used as context"
    )

    # Metadata
    message_metadata: Mapped[dict] = mapped_column(
        "metadata",
        JSON,
        nullable=False,
        default=dict,
        comment="Message metadata (tokens, model, etc.)"
    )

    # Relationships
    session: Mapped["ChatSessionModel"] = relationship(
        "ChatSessionModel",
        back_populates="messages"
    )

    # Table constraints
    __table_args__ = (
        CheckConstraint("sequence_number >= 0",
                        name="non_negative_sequence_number"),
        CheckConstraint(
            "role IN ('user', 'assistant', 'system')", name="valid_role"),
        Index("idx_messages_session_sequence",
              "session_id", "sequence_number"),
        UniqueConstraint("session_id", "sequence_number",
                         name="unique_message_sequence"),
    )

    def __repr__(self) -> str:
        return f"<ChatMessage(id={self.id}, role={self.role}, session_id={self.session_id})>"
