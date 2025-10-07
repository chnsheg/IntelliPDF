"""
Security and authentication utilities for IntelliPDF application.

This module provides JWT token management, password hashing,
and authentication middleware.
"""

from datetime import datetime, timedelta
from typing import Any, Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from .config import Settings, get_settings
from .exceptions import TokenExpiredError, TokenInvalidError

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.

    Args:
        plain_password: Plain text password
        hashed_password: Hashed password

    Returns:
        bool: True if password matches
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: Plain text password

    Returns:
        str: Hashed password
    """
    return pwd_context.hash(password)


def create_access_token(
    data: dict[str, Any],
    expires_delta: Optional[timedelta] = None,
    settings: Optional[Settings] = None
) -> str:
    """
    Create a JWT access token.

    Args:
        data: Token payload data
        expires_delta: Optional custom expiration time
        settings: Optional settings override

    Returns:
        str: Encoded JWT token
    """
    if settings is None:
        settings = get_settings()

    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.access_token_expire_minutes
        )

    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow()
    })

    encoded_jwt = jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.algorithm
    )

    return encoded_jwt


def decode_access_token(
    token: str,
    settings: Optional[Settings] = None
) -> dict[str, Any]:
    """
    Decode and validate a JWT access token.

    Args:
        token: JWT token string
        settings: Optional settings override

    Returns:
        dict: Token payload

    Raises:
        TokenExpiredError: If token has expired
        TokenInvalidError: If token is invalid
    """
    if settings is None:
        settings = get_settings()

    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm]
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise TokenExpiredError("Access token has expired")
    except JWTError as e:
        raise TokenInvalidError(f"Invalid access token: {str(e)}")


def generate_api_key() -> str:
    """
    Generate a secure random API key.

    Returns:
        str: Random API key
    """
    import secrets
    return secrets.token_urlsafe(32)
