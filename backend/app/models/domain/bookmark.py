"""
Bookmark domain model

Domain logic for bookmark entities with AI-generated summaries.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4


@dataclass
class Bookmark:
    """
    Bookmark domain entity

    Represents a user-created bookmark with AI-generated summary
    based on selected text and conversation history.
    """

    user_id: UUID
    document_id: UUID
    chunk_id: Optional[UUID]  # Associated chunk if exists

    # Text selection
    selected_text: str
    page_number: int

    # Position information (bounding box)
    position_x: float
    position_y: float
    position_width: float
    position_height: float

    # AI-generated content
    ai_summary: str  # AI-generated bookmark summary

    # Metadata
    id: UUID = field(default_factory=uuid4)
    title: Optional[str] = None  # User-provided or AI-generated title
    user_notes: Optional[str] = None  # User's additional notes
    # Associated chat history
    conversation_context: Optional[Dict[str, Any]] = None
    tags: List[str] = field(default_factory=list)  # User-defined tags
    color: str = "#FCD34D"  # Highlight color (default: yellow)

    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        """Validate bookmark data after initialization."""
        if not self.selected_text or len(self.selected_text.strip()) == 0:
            raise ValueError("Selected text cannot be empty")

        if self.page_number < 0:
            raise ValueError("Page number must be non-negative")

        if not self.ai_summary or len(self.ai_summary.strip()) == 0:
            raise ValueError("AI summary is required")

        # Validate position
        if self.position_x < 0 or self.position_y < 0:
            raise ValueError("Position coordinates must be non-negative")

        if self.position_width <= 0 or self.position_height <= 0:
            raise ValueError("Position dimensions must be positive")

    def update_summary(self, new_summary: str):
        """
        Update AI-generated summary.

        Args:
            new_summary: New summary text
        """
        if not new_summary or len(new_summary.strip()) == 0:
            raise ValueError("Summary cannot be empty")

        self.ai_summary = new_summary
        self.updated_at = datetime.utcnow()

    def add_note(self, note: str):
        """
        Add user note to bookmark.

        Args:
            note: User's note text
        """
        self.user_notes = note
        self.updated_at = datetime.utcnow()

    def add_tag(self, tag: str):
        """
        Add a tag to bookmark.

        Args:
            tag: Tag name
        """
        if tag and tag not in self.tags:
            self.tags.append(tag)
            self.updated_at = datetime.utcnow()

    def remove_tag(self, tag: str):
        """
        Remove a tag from bookmark.

        Args:
            tag: Tag name to remove
        """
        if tag in self.tags:
            self.tags.remove(tag)
            self.updated_at = datetime.utcnow()

    def set_color(self, color: str):
        """
        Set highlight color.

        Args:
            color: Hex color code
        """
        # Validate hex color format
        if not color.startswith('#') or len(color) not in [4, 7]:
            raise ValueError("Invalid hex color format")

        self.color = color
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert bookmark to dictionary."""
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'document_id': str(self.document_id),
            'chunk_id': str(self.chunk_id) if self.chunk_id else None,
            'selected_text': self.selected_text,
            'page_number': self.page_number,
            'position': {
                'x': self.position_x,
                'y': self.position_y,
                'width': self.position_width,
                'height': self.position_height
            },
            'ai_summary': self.ai_summary,
            'title': self.title,
            'user_notes': self.user_notes,
            'conversation_context': self.conversation_context,
            'tags': self.tags,
            'color': self.color,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
