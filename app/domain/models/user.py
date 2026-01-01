"""User domain models."""

from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    """Base user model."""

    email: EmailStr
    username: str = Field(..., min_length=3, max_length=100)


class UserCreate(UserBase):
    """User creation model."""

    password: str = Field(..., min_length=8, max_length=72, description="Password (8-72 bytes, bcrypt limitation)")


class UserUpdate(BaseModel):
    """User update model."""

    email: EmailStr | None = None
    username: str | None = Field(None, min_length=3, max_length=100)
    is_active: bool | None = None


class UserInDB(UserBase):
    """User in database model."""

    id: str
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class User(UserInDB):
    """Public user model."""

    pass


class UserLogin(BaseModel):
    """User login model."""

    email: EmailStr
    password: str


class Token(BaseModel):
    """Token model."""

    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token data model."""

    user_id: str | None = None

