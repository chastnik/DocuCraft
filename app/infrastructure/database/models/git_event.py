"""Git event database model."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import String, ForeignKey, Boolean, DateTime, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.infrastructure.database.base import Base, TimestampMixin, generate_uuid

if TYPE_CHECKING:
    from app.infrastructure.database.models.project import Project
    from app.infrastructure.database.models.ai_suggestion import AISuggestion


class GitEvent(Base):
    """Git event model."""

    __tablename__ = "git_events"

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
    event_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # push, merge, etc.
    commit_hash: Mapped[str | None] = mapped_column(String(40), nullable=True, index=True)
    branch: Mapped[str | None] = mapped_column(String(255), nullable=True)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)  # Full webhook payload
    processed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="git_events")
    ai_suggestions: Mapped[list["AISuggestion"]] = relationship(
        "AISuggestion",
        back_populates="git_event",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<GitEvent(id={self.id}, event_type={self.event_type}, processed={self.processed})>"

