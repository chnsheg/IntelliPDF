"""
User domain model

Domain logic for user entities with authentication and authorization.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4


@dataclass
class User:
    """
    User domain entity

    Represents a user in the system with authentication credentials.
    """

    username: str
    email: str
    hashed_password: str
    id: UUID = field(default_factory=uuid4)
    full_name: Optional[str] = None
    is_active: bool = True
    is_superuser: bool = False
    gemini_api_key: Optional[str] = None  # User's encrypted API key
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    last_login_at: Optional[datetime] = None

    def __post_init__(self):
        """Validate user data after initialization."""
        if not self.username or len(self.username) < 3:
            raise ValueError("Username must be at least 3 characters")

        if not self.email or '@' not in self.email:
            raise ValueError("Invalid email address")

        if not self.hashed_password:
            raise ValueError("Password hash is required")

    def activate(self):
        """Activate user account."""
        self.is_active = True
        self.updated_at = datetime.utcnow()

    def deactivate(self):
        """Deactivate user account."""
        self.is_active = False
        self.updated_at = datetime.utcnow()

    def update_last_login(self):
        """Update last login timestamp."""
        self.last_login_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def update_profile(self, full_name: Optional[str] = None, email: Optional[str] = None):
        """
        Update user profile information.

        Args:
            full_name: New full name
            email: New email address
        """
        if full_name is not None:
            self.full_name = full_name

        if email is not None:
            if '@' not in email:
                raise ValueError("Invalid email address")
            self.email = email

        self.updated_at = datetime.utcnow()

    def set_gemini_api_key(self, api_key: str):
        """
        Set user's Gemini API key (should be encrypted before storing).

        Args:
            api_key: Encrypted API key string
        """
        self.gemini_api_key = api_key
        self.updated_at = datetime.utcnow()
