"""
SQLAlchemy base class and common functionality.

This module provides the declarative base and common mixins for all database models.
"""

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """
    Base class for all database models.

    Provides common functionality and type annotations for SQLAlchemy models.
    """

    # Allow SQLAlchemy to use Python type hints
    type_annotation_map = {}


class TimestampMixin:
    """
    Mixin for automatic timestamp management.

    Adds created_at and updated_at columns with automatic values.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Record creation timestamp"
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Record last update timestamp"
    )
