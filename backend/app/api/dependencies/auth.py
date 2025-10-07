"""
Authentication dependencies for FastAPI endpoints.

Provides dependency injection for authentication and authorization.
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..core.auth import AuthUtils
from ..core.exceptions import AuthenticationError
from ..models.db import UserModel
from ..repositories.user_repository import UserRepository
from ..services.auth_service import AuthService

# HTTP Bearer token scheme
security = HTTPBearer()


async def get_user_repository(db: AsyncSession = Depends(get_db)) -> UserRepository:
    """
    Get user repository instance.

    Args:
        db: Database session

    Returns:
        UserRepository instance
    """
    return UserRepository(db)


async def get_auth_service(
    user_repo: UserRepository = Depends(get_user_repository)
) -> AuthService:
    """
    Get authentication service instance.

    Args:
        user_repo: User repository

    Returns:
        AuthService instance
    """
    return AuthService(user_repo)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
) -> UserModel:
    """
    Get current authenticated user from JWT token.

    Args:
        credentials: HTTP authorization credentials
        auth_service: Authentication service

    Returns:
        Current user model

    Raises:
        HTTPException: If authentication fails
    """
    token = credentials.credentials
    
    try:
        user = await auth_service.get_current_user(token)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_active_user(
    current_user: UserModel = Depends(get_current_user)
) -> UserModel:
    """
    Get current active user (must be active).

    Args:
        current_user: Current user from token

    Returns:
        Active user model

    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user


async def get_current_superuser(
    current_user: UserModel = Depends(get_current_active_user)
) -> UserModel:
    """
    Get current superuser (must be active and superuser).

    Args:
        current_user: Current active user

    Returns:
        Superuser model

    Raises:
        HTTPException: If user is not superuser
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user


def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[str]:
    """
    Get optional current user ID (for public endpoints).

    Args:
        credentials: Optional HTTP authorization credentials

    Returns:
        User ID or None if not authenticated
    """
    if credentials is None:
        return None
    
    token = credentials.credentials
    try:
        return AuthUtils.get_user_id_from_token(token)
    except:
        return None
