"""AI Configuration database model."""

from sqlalchemy import String, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from app.infrastructure.database.base import Base, TimestampMixin, generate_uuid


class AIConfiguration(Base, TimestampMixin):
    """AI Configuration model for storing AI provider settings."""

    __tablename__ = "ai_configurations"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=generate_uuid,
    )
    # Provider name: "openai" or "anthropic"
    provider: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    # API key (encrypted or plain text - в продакшене лучше шифровать)
    api_key: Mapped[str] = mapped_column(Text, nullable=False)
    # Additional configuration as JSON (можно расширить в будущем)
    config: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Is this configuration active
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    def __repr__(self) -> str:
        return f"<AIConfiguration(id={self.id}, provider={self.provider}, is_active={self.is_active})>"

