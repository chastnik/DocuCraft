"""AI suggestion database model."""

import enum
from datetime import datetime
from sqlalchemy import String, ForeignKey, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.infrastructure.database.base import Base, TimestampMixin, generate_uuid


class SuggestionType(str, enum.Enum):
    """AI suggestion types."""

    UPDATE = "update"
    ADD = "add"
    DELETE = "delete"


class SuggestionStatus(str, enum.Enum):
    """AI suggestion status."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    APPLIED = "applied"


class AISuggestion(Base):
    """AI suggestion model."""

    __tablename__ = "ai_suggestions"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=generate_uuid,
    )
    document_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    git_event_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("git_events.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    suggestion_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    target_section: Mapped[str | None] = mapped_column(String(255), nullable=True)
    suggested_content: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20),
        default=SuggestionStatus.PENDING.value,
        nullable=False,
        index=True,
    )
    reviewed_by_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    document: Mapped["Document"] = relationship("Document", back_populates="ai_suggestions")
    git_event: Mapped["GitEvent | None"] = relationship("GitEvent", back_populates="ai_suggestions")
    reviewed_by: Mapped["User | None"] = relationship("User", foreign_keys=[reviewed_by_id])

    def __repr__(self) -> str:
        return f"<AISuggestion(id={self.id}, type={self.suggestion_type}, status={self.status})>"

