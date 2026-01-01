"""Project database models."""

import enum
from sqlalchemy import String, ForeignKey, Enum, UniqueConstraint, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.infrastructure.database.base import Base, TimestampMixin, generate_uuid


class ProjectRole(str, enum.Enum):
    """Project member roles."""

    VIEWER = "Viewer"
    EDITOR = "Editor"
    PROJECT_LEAD = "ProjectLead"
    ADMIN = "Admin"


class AIMode(str, enum.Enum):
    """AI processing mode."""

    SUGGEST_ONLY = "suggest-only"
    AUTO_APPLY = "auto-apply"


class GitProvider(str, enum.Enum):
    """Git provider types."""

    GITHUB = "github"
    GITLAB = "gitlab"
    GITEA = "gitea"
    CUSTOM = "custom"


class Project(Base, TimestampMixin):
    """Project model."""

    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=generate_uuid,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    owner_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Legacy fields (deprecated, kept for backward compatibility)
    github_repo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    github_webhook_secret: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # New Git configuration fields (per-project settings)
    git_provider: Mapped[GitProvider | None] = mapped_column(
        Enum(GitProvider),
        nullable=True,
    )
    git_repo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    git_api_base_url: Mapped[str | None] = mapped_column(String(500), nullable=True)  # For custom Git servers
    git_access_token: Mapped[str | None] = mapped_column(Text, nullable=True)  # Encrypted token
    git_webhook_secret: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ai_mode: Mapped[AIMode] = mapped_column(
        Enum(AIMode),
        default=AIMode.SUGGEST_ONLY,
        nullable=False,
    )

    # Relationships
    owner: Mapped["User"] = relationship(
        "User",
        back_populates="owned_projects",
        foreign_keys=[owner_id],
    )
    members: Mapped[list["ProjectMember"]] = relationship(
        "ProjectMember",
        back_populates="project",
        cascade="all, delete-orphan",
    )
    documents: Mapped[list["Document"]] = relationship(
        "Document",
        back_populates="project",
        cascade="all, delete-orphan",
    )
    git_events: Mapped[list["GitEvent"]] = relationship(
        "GitEvent",
        back_populates="project",
        cascade="all, delete-orphan",
    )
    openapi_specs: Mapped[list["OpenAPISpec"]] = relationship(
        "OpenAPISpec",
        back_populates="project",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Project(id={self.id}, name={self.name})>"


class ProjectMember(Base, TimestampMixin):
    """Project member model."""

    __tablename__ = "project_members"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=generate_uuid,
    )
    project_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[ProjectRole] = mapped_column(
        Enum(ProjectRole),
        default=ProjectRole.VIEWER,
        nullable=False,
    )

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="members")
    user: Mapped["User"] = relationship("User", back_populates="project_memberships")

    __table_args__ = (
        UniqueConstraint("project_id", "user_id", name="uq_project_member"),
    )

    def __repr__(self) -> str:
        return f"<ProjectMember(project_id={self.project_id}, user_id={self.user_id}, role={self.role})>"

