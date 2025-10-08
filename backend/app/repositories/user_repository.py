"""
User repository for database operations.

This module provides data access methods for user entities.
"""

from typing import Optional
from sqlalchemy import select

from .base_repository import BaseRepository
from ..models.db import UserModel
from ..core.logging import get_logger

logger = get_logger(__name__)


class UserRepository(BaseRepository[UserModel]):
    """Repository for user database operations."""

    def __init__(self, session):
        """
        Initialize user repository.

        Args:
            session: Async database session
        """
        super().__init__(UserModel, session)

    async def get_by_username(self, username: str) -> Optional[UserModel]:
        """
        Get user by username.

        Args:
            username: Username to search for

        Returns:
            User model or None if not found
        """
        try:
            stmt = select(UserModel).where(UserModel.username == username)
            result = await self.session.execute(stmt)
            user = result.scalar_one_or_none()

            if user:
                logger.info(f"Found user by username: {username}")
            else:
                logger.debug(f"User not found by username: {username}")

            return user
        except Exception as e:
            logger.error(f"Error getting user by username: {e}")
            raise

    async def get_by_email(self, email: str) -> Optional[UserModel]:
        """
        Get user by email.

        Args:
            email: Email to search for

        Returns:
            User model or None if not found
        """
        try:
            stmt = select(UserModel).where(UserModel.email == email)
            result = await self.session.execute(stmt)
            user = result.scalar_one_or_none()

            if user:
                logger.info(f"Found user by email: {email}")
            else:
                logger.debug(f"User not found by email: {email}")

            return user
        except Exception as e:
            logger.error(f"Error getting user by email: {e}")
            raise

    async def check_username_exists(self, username: str) -> bool:
        """
        Check if username already exists.

        Args:
            username: Username to check

        Returns:
            True if exists, False otherwise
        """
        user = await self.get_by_username(username)
        return user is not None

    async def check_email_exists(self, email: str) -> bool:
        """
        Check if email already exists.

        Args:
            email: Email to check

        Returns:
            True if exists, False otherwise
        """
        user = await self.get_by_email(email)
        return user is not None

    async def update_last_login(self, user_id: str) -> bool:
        """
        Update user's last login timestamp.

        Args:
            user_id: User ID

        Returns:
            True if updated, False otherwise
        """
        from datetime import datetime

        try:
            user = await self.get_by_id(user_id)
            if not user:
                return False

            user.last_login_at = datetime.utcnow()
            await self.session.flush()

            logger.info(f"Updated last login for user: {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error updating last login: {e}")
            raise

    async def activate_user(self, user_id: str) -> bool:
        """
        Activate user account.

        Args:
            user_id: User ID

        Returns:
            True if activated, False otherwise
        """
        try:
            user = await self.get_by_id(user_id)
            if not user:
                return False

            user.is_active = True
            await self.session.flush()

            logger.info(f"Activated user: {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error activating user: {e}")
            raise

    async def deactivate_user(self, user_id: str) -> bool:
        """
        Deactivate user account.

        Args:
            user_id: User ID

        Returns:
            True if deactivated, False otherwise
        """
        try:
            user = await self.get_by_id(user_id)
            if not user:
                return False

            user.is_active = False
            await self.session.flush()

            logger.info(f"Deactivated user: {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error deactivating user: {e}")
            raise
