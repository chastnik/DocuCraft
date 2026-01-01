"""AI Configuration domain models."""

from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field, field_validator


class AIConfigurationBase(BaseModel):
    """Base AI configuration model."""

    provider: Literal["openai", "anthropic"] = Field(..., description="AI provider name")
    api_key: str = Field(..., min_length=1, description="API key for the provider")
    config: str | None = Field(None, description="Additional JSON configuration")
    is_active: bool = Field(True, description="Is this configuration active")


class AIConfigurationCreate(AIConfigurationBase):
    """AI configuration creation model."""

    pass


class AIConfigurationUpdate(BaseModel):
    """AI configuration update model."""

    provider: Literal["openai", "anthropic"] | None = None
    api_key: str | None = Field(None, min_length=1)
    config: str | None = None
    is_active: bool | None = None


class AIConfigurationInDB(AIConfigurationBase):
    """AI configuration in database model."""

    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AIConfiguration(AIConfigurationInDB):
    """Public AI configuration model."""

    pass


class AIConfigurationResponse(BaseModel):
    """AI configuration response model (without sensitive data)."""

    id: str
    provider: Literal["openai", "anthropic"]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    # API key is masked for security
    api_key_masked: str = Field(..., description="Masked API key (shows only last 4 characters)")

    class Config:
        from_attributes = True

