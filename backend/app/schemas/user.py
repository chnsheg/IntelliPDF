"""
Authentication and user-related Pydantic schemas.

Request/response models for authentication endpoints.
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, validator


# ==================== User Schemas ====================

class UserBase(BaseModel):
    """Base user schema with common fields."""

    username: str = Field(..., min_length=3, max_length=50,
                          description="Unique username")
    email: EmailStr = Field(..., description="User email address")
    full_name: Optional[str] = Field(
        None, max_length=100, description="User's full name")


class UserCreate(UserBase):
    """Schema for user registration."""

    password: str = Field(..., min_length=6, max_length=100,
                          description="User password")

    @validator('password')
    def validate_password(cls, v):
        """Validate password strength."""
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters long')
        return v


class UserUpdate(BaseModel):
    """Schema for user profile update."""

    full_name: Optional[str] = Field(None, max_length=100)
    email: Optional[EmailStr] = None
    gemini_api_key: Optional[str] = None


class UserResponse(UserBase):
    """Schema for user response (excludes sensitive data)."""

    id: str = Field(..., description="User ID")
    is_active: bool = Field(..., description="Whether user is active")
    is_superuser: bool = Field(..., description="Whether user is superuser")
    created_at: datetime = Field(..., description="Account creation time")
    last_login_at: Optional[datetime] = Field(
        None, description="Last login time")

    class Config:
        from_attributes = True


# ==================== Authentication Schemas ====================

class LoginRequest(BaseModel):
    """Schema for login request."""

    username: str = Field(..., description="Username or email")
    password: str = Field(..., description="User password")


class LoginResponse(BaseModel):
    """Schema for login response."""

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    user: UserResponse = Field(..., description="User information")


class RegisterRequest(UserCreate):
    """Schema for registration request (same as UserCreate)."""
    pass


class RegisterResponse(LoginResponse):
    """Schema for registration response (same as LoginResponse)."""
    pass


class PasswordChangeRequest(BaseModel):
    """Schema for password change request."""

    old_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=6, description="New password")

    @validator('new_password')
    def validate_new_password(cls, v):
        """Validate new password strength."""
        if len(v) < 6:
            raise ValueError('New password must be at least 6 characters long')
        return v


class TokenPayload(BaseModel):
    """Schema for JWT token payload."""

    sub: str = Field(..., description="User ID (subject)")
    username: str = Field(..., description="Username")
    exp: Optional[datetime] = Field(None, description="Expiration time")
    iat: Optional[datetime] = Field(None, description="Issued at time")


# ==================== API Response Schemas ====================

class MessageResponse(BaseModel):
    """Generic message response."""

    message: str = Field(..., description="Response message")
    success: bool = Field(default=True, description="Operation success status")
