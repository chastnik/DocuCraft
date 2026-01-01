"""Document domain models."""

from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field, field_validator
from app.core.validation import DocumentContentValidator


class DocumentBase(BaseModel):
    """Base document model."""

    title: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1)  # Markdown
    content_json: dict[str, Any] | None = None  # Structured for editor

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        """Validate slug format."""
        from app.core.validation import validate_slug

        if not validate_slug(v):
            raise ValueError(
                "Slug can only contain lowercase letters, numbers, hyphens, and underscores"
            )
        return v

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        """Validate content length."""
        is_valid, error = DocumentContentValidator.validate_content(v)
        if not is_valid:
            raise ValueError(error)
        return v


class DocumentCreate(DocumentBase):
    """Document creation model."""

    project_id: str


class DocumentUpdate(BaseModel):
    """Document update model."""

    title: str | None = Field(None, min_length=1, max_length=255)
    slug: str | None = Field(None, min_length=1, max_length=255)
    content: str | None = Field(None, min_length=1)
    content_json: dict[str, Any] | None = None

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str | None) -> str | None:
        """Validate slug format."""
        if v is None:
            return v
        from app.core.validation import validate_slug

        if not validate_slug(v):
            raise ValueError(
                "Slug can only contain lowercase letters, numbers, hyphens, and underscores"
            )
        return v

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str | None) -> str | None:
        """Validate content length."""
        if v is None:
            return v
        is_valid, error = DocumentContentValidator.validate_content(v)
        if not is_valid:
            raise ValueError(error)
        return v


class DocumentInDB(DocumentBase):
    """Document in database model."""

    id: str
    project_id: str
    version: int
    git_commit_hash: str | None
    created_by_id: str | None
    updated_by_id: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class Document(DocumentInDB):
    """Public document model."""

    pass


class DocumentVersionBase(BaseModel):
    """Base document version model."""

    version_number: int
    content: str
    content_json: dict[str, Any] | None = None
    git_commit_hash: str | None = None
    change_summary: str | None = None


class DocumentVersionCreate(DocumentVersionBase):
    """Document version creation model."""

    document_id: str
    changed_by_id: str | None = None


class DocumentVersionInDB(DocumentVersionBase):
    """Document version in database model."""

    id: str
    document_id: str
    changed_by_id: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentVersion(DocumentVersionInDB):
    """Public document version model."""

    pass
