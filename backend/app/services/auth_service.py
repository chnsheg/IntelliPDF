"""
Authentication service for user registration and login.

This service handles user authentication operations.
"""

from typing import Optional, Tuple
from datetime import timedelta

from ..core.auth import AuthUtils
from ..core.logging import get_logger
from ..core.exceptions import AuthenticationError, ValidationError
from ..models.db import UserModel
from ..repositories.user_repository import UserRepository

logger = get_logger(__name__)


class AuthService:
    """Service for user authentication operations."""

    def __init__(self, user_repo: UserRepository):
        """
        Initialize authentication service.

        Args:
            user_repo: User repository instance
        """
        self.user_repo = user_repo
        self.auth_utils = AuthUtils()

    async def register_user(
        self,
        username: str,
        email: str,
        password: str,
        full_name: Optional[str] = None
    ) -> Tuple[UserModel, str]:
        """
        Register a new user.

        Args:
            username: Unique username
            email: User email
            password: Plain text password
            full_name: Optional full name

        Returns:
            Tuple of (created user, access token)

        Raises:
            ValidationError: If username or email already exists
        """
        # Validate username length
        if len(username) < 3:
            raise ValidationError("Username must be at least 3 characters")

        if len(password) < 6:
            raise ValidationError("Password must be at least 6 characters")

        # Check if username exists
        if await self.user_repo.check_username_exists(username):
            raise ValidationError(f"Username '{username}' already exists")

        # Check if email exists
        if await self.user_repo.check_email_exists(email):
            raise ValidationError(f"Email '{email}' already registered")

        # Hash password
        hashed_password = self.auth_utils.hash_password(password)

        # Create user
        user = UserModel(
            username=username,
            email=email,
            hashed_password=hashed_password,
            full_name=full_name,
            is_active=True,
            is_superuser=False
        )

        created_user = await self.user_repo.create(user)
        await self.user_repo.commit()

        logger.info(f"User registered: {username} ({email})")

        # Generate access token
        access_token = self.auth_utils.create_access_token(
            data={"sub": created_user.id, "username": username}
        )

        return created_user, access_token

    async def authenticate_user(
        self,
        username: str,
        password: str
    ) -> Tuple[UserModel, str]:
        """
        Authenticate user and generate access token.

        Args:
            username: Username or email
            password: Plain text password

        Returns:
            Tuple of (user, access token)

        Raises:
            AuthenticationError: If credentials are invalid
        """
        # Try to find user by username or email
        user = await self.user_repo.get_by_username(username)
        if not user:
            user = await self.user_repo.get_by_email(username)

        if not user:
            logger.warning(f"Login attempt for non-existent user: {username}")
            raise AuthenticationError("Invalid username or password")

        # Check if user is active
        if not user.is_active:
            logger.warning(f"Login attempt for inactive user: {username}")
            raise AuthenticationError("User account is inactive")

        # Verify password
        if not self.auth_utils.verify_password(password, user.hashed_password):
            logger.warning(f"Invalid password for user: {username}")
            raise AuthenticationError("Invalid username or password")

        # Update last login
        await self.user_repo.update_last_login(user.id)
        await self.user_repo.commit()

        logger.info(f"User authenticated: {username}")

        # Generate access token
        access_token = self.auth_utils.create_access_token(
            data={"sub": user.id, "username": user.username},
            expires_delta=timedelta(days=7)
        )

        return user, access_token

    async def get_current_user(self, token: str) -> Optional[UserModel]:
        """
        Get current user from JWT token.

        Args:
            token: JWT access token

        Returns:
            User model or None if invalid

        Raises:
            AuthenticationError: If token is invalid
        """
        try:
            # Decode token
            payload = self.auth_utils.decode_token(token)
            user_id: str = payload.get("sub")

            if user_id is None:
                raise AuthenticationError("Invalid token payload")

            # Get user from database
            user = await self.user_repo.get_by_id(user_id)
            if user is None:
                raise AuthenticationError("User not found")

            if not user.is_active:
                raise AuthenticationError("User account is inactive")

            return user

        except AuthenticationError:
            raise
        except Exception as e:
            logger.error(f"Error getting current user: {e}")
            raise AuthenticationError("Failed to authenticate user")

    async def change_password(
        self,
        user_id: str,
        old_password: str,
        new_password: str
    ) -> bool:
        """
        Change user password.

        Args:
            user_id: User ID
            old_password: Current password
            new_password: New password

        Returns:
            True if successful

        Raises:
            AuthenticationError: If old password is incorrect
            ValidationError: If new password is invalid
        """
        if len(new_password) < 6:
            raise ValidationError("Password must be at least 6 characters")

        # Get user
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise AuthenticationError("User not found")

        # Verify old password
        if not self.auth_utils.verify_password(old_password, user.hashed_password):
            raise AuthenticationError("Incorrect current password")

        # Hash new password
        hashed_password = self.auth_utils.hash_password(new_password)

        # Update user
        await self.user_repo.update(user_id, {"hashed_password": hashed_password})
        await self.user_repo.commit()

        logger.info(f"Password changed for user: {user_id}")
        return True
