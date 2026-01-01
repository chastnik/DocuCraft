"""Project domain models."""

from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field, field_validator, model_validator
from app.core.validation import validate_github_url, validate_git_url


class ProjectBase(BaseModel):
    """Base project model."""

    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(None, max_length=1000)
    github_repo_url: str | None = Field(None, max_length=500)  # Deprecated, use git_repo_url
    ai_mode: Literal["suggest-only", "auto-apply"] = "suggest-only"

    @field_validator("github_repo_url")
    @classmethod
    def validate_github_url(cls, v: str | None) -> str | None:
        """Validate GitHub repository URL."""
        if v is None:
            return v
        if not validate_github_url(v):
            raise ValueError("Invalid GitHub repository URL format")
        return v


class GitConfiguration(BaseModel):
    """Git configuration for a project."""

    provider: Literal["github", "gitlab", "gitea", "custom"] | None = Field(None, description="Git provider type")
    repo_url: str | None = Field(None, max_length=500, description="Repository URL")
    api_base_url: str | None = Field(None, max_length=500, description="API base URL for custom Git servers")
    access_token: str | None = Field(None, description="Access token for Git API (will be encrypted)")
    webhook_secret: str | None = Field(None, max_length=255, description="Webhook secret for verifying webhook events")

    @model_validator(mode="after")
    def validate_git_config(self):
        """Validate Git configuration."""
        if self.repo_url and not self.provider:
            # Try to detect provider from URL
            if "github.com" in self.repo_url:
                self.provider = "github"
            elif "gitlab.com" in self.repo_url or "gitlab" in self.repo_url.lower():
                self.provider = "gitlab"
            else:
                # For unknown URLs, require explicit provider
                raise ValueError("Provider must be specified for custom Git repositories")

        if self.repo_url:
            if not validate_git_url(self.repo_url, self.provider):
                raise ValueError(f"Invalid {self.provider or 'Git'} repository URL format")

        if self.provider == "custom" and not self.api_base_url:
            raise ValueError("api_base_url is required for custom Git provider")

        return self


class ProjectCreate(ProjectBase):
    """Project creation model."""

    pass


class ProjectUpdate(BaseModel):
    """Project update model."""

    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None, max_length=1000)
    github_repo_url: str | None = Field(None, max_length=500)  # Deprecated
    ai_mode: Literal["suggest-only", "auto-apply"] | None = None

    @field_validator("github_repo_url")
    @classmethod
    def validate_github_url(cls, v: str | None) -> str | None:
        """Validate GitHub repository URL."""
        if v is None:
            return v
        if not validate_github_url(v):
            raise ValueError("Invalid GitHub repository URL format")
        return v


class ProjectInDB(ProjectBase):
    """Project in database model."""

    id: str
    owner_id: str
    github_webhook_secret: str | None  # Deprecated
    # Git configuration fields
    git_provider: Literal["github", "gitlab", "gitea", "custom"] | None = None
    git_repo_url: str | None = None
    git_api_base_url: str | None = None
    git_webhook_secret: str | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class Project(ProjectInDB):
    """Public project model."""

    pass


class ProjectMemberBase(BaseModel):
    """Base project member model."""

    role: Literal["Viewer", "Editor", "ProjectLead", "Admin"] = "Viewer"


class ProjectMemberCreate(ProjectMemberBase):
    """Project member creation model."""

    user_id: str


class ProjectMemberUpdate(BaseModel):
    """Project member update model."""

    role: Literal["Viewer", "Editor", "ProjectLead", "Admin"] | None = None


class ProjectMemberInDB(ProjectMemberBase):
    """Project member in database model."""

    id: str
    project_id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProjectMember(ProjectMemberInDB):
    """Public project member model."""

    pass


class ProjectWithMembers(Project):
    """Project with members."""

    members: list[ProjectMember] = []
