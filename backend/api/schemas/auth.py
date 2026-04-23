import re
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator


# Request/Response Models
class UserRegisterRequest(BaseModel):
    """User registration request"""
    email: EmailStr
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=12)

    @field_validator("username")
    @classmethod
    def validate_username(cls, v):
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError("Username can only contain letters, numbers, underscores, and hyphens")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in v):
            raise ValueError("Password must contain at least one special character")
        return v


class UserResponse(BaseModel):
    """User response model"""
    id: str
    email: str
    username: str
    is_active: bool
    is_verified: bool
    roles: list[str]
    created_at: datetime


class LoginRequest(BaseModel):
    """Login request"""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshTokenRequest(BaseModel):
    """Token refresh request"""
    refresh_token: str


class PasswordResetRequest(BaseModel):
    """Password reset request"""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation"""
    token: str
    new_password: str = Field(min_length=12)


class APIKeyCreateRequest(BaseModel):
    """API key creation request"""
    name: str = Field(min_length=3, max_length=100)
    scopes: list[str] = ["read"]
    expires_in_days: int | None = Field(default=None, ge=1, le=365)


class APIKeyResponse(BaseModel):
    """API key response"""
    id: str
    key: str | None = None  # Only returned on creation
    name: str
    scopes: list[str]
    created_at: datetime
    expires_at: datetime | None


class APIKeyListItem(BaseModel):
    """API key list item (without the actual key)"""
    id: str
    name: str
    scopes: list[str]
    created_at: datetime
    expires_at: datetime | None
    last_used: datetime | None
