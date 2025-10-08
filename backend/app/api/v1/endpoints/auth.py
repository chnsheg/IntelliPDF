"""
Authentication API endpoints.

Handles user registration, login, and authentication operations.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ....core.dependencies import get_db
from ....core.logging import get_logger
from ....core.exceptions import AuthenticationError, ValidationError
from ....services.auth_service import AuthService
from ....repositories.user_repository import UserRepository
from ....schemas.user import (
    RegisterRequest,
    RegisterResponse,
    LoginRequest,
    LoginResponse,
    UserResponse,
    PasswordChangeRequest,
    MessageResponse
)
from ....models.db import UserModel
from ...dependencies.auth import (
    get_auth_service,
    get_current_active_user
)

router = APIRouter(prefix="/auth", tags=["Authentication"])
logger = get_logger(__name__)


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user",
    description="Create a new user account with username, email and password"
)
async def register(
    user_data: RegisterRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Register a new user account.

    Args:
        user_data: User registration data
        auth_service: Authentication service

    Returns:
        User information and access token

    Raises:
        HTTPException: If registration fails
    """
    try:
        user, access_token = await auth_service.register_user(
            username=user_data.username,
            email=user_data.email,
            password=user_data.password,
            full_name=user_data.full_name
        )

        logger.info(f"User registered successfully: {user.username}")

        return RegisterResponse(
            access_token=access_token,
            token_type="bearer",
            user=UserResponse.model_validate(user)
        )

    except ValidationError as e:
        logger.warning(f"Registration validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Registration error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register user"
        )


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="User login",
    description="Authenticate user and get access token"
)
async def login(
    login_data: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Authenticate user and generate access token.

    Args:
        login_data: Login credentials
        auth_service: Authentication service

    Returns:
        User information and access token

    Raises:
        HTTPException: If authentication fails
    """
    try:
        user, access_token = await auth_service.authenticate_user(
            username=login_data.username,
            password=login_data.password
        )

        logger.info(f"User logged in: {user.username}")

        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            user=UserResponse.model_validate(user)
        )

    except AuthenticationError as e:
        logger.warning(f"Login failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"}
        )
    except Exception as e:
        logger.error(f"Login error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to authenticate user"
        )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user",
    description="Get information about currently authenticated user"
)
async def get_me(
    current_user: UserModel = Depends(get_current_active_user)
):
    """
    Get current user information.

    Args:
        current_user: Current authenticated user

    Returns:
        User information
    """
    return UserResponse.model_validate(current_user)


@router.post(
    "/change-password",
    response_model=MessageResponse,
    summary="Change password",
    description="Change password for currently authenticated user"
)
async def change_password(
    password_data: PasswordChangeRequest,
    current_user: UserModel = Depends(get_current_active_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Change user password.

    Args:
        password_data: Password change data
        current_user: Current authenticated user
        auth_service: Authentication service

    Returns:
        Success message

    Raises:
        HTTPException: If password change fails
    """
    try:
        await auth_service.change_password(
            user_id=current_user.id,
            old_password=password_data.old_password,
            new_password=password_data.new_password
        )

        logger.info(f"Password changed for user: {current_user.username}")

        return MessageResponse(
            message="Password changed successfully",
            success=True
        )

    except AuthenticationError as e:
        logger.warning(f"Password change failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except ValidationError as e:
        logger.warning(f"Password validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Password change error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change password"
        )


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="User logout",
    description="Logout current user (client should discard token)"
)
async def logout(
    current_user: UserModel = Depends(get_current_active_user)
):
    """
    Logout user (client-side token removal).

    Note: JWT tokens are stateless, so logout is handled on the client side
    by discarding the token. This endpoint is provided for consistency.

    Args:
        current_user: Current authenticated user

    Returns:
        Success message
    """
    logger.info(f"User logged out: {current_user.username}")

    return MessageResponse(
        message="Logged out successfully",
        success=True
    )
