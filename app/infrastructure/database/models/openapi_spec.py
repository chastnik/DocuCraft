"""OpenAPI spec database model."""

from sqlalchemy import String, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.infrastructure.database.base import Base, TimestampMixin, generate_uuid


class OpenAPISpec(Base, TimestampMixin):
    """OpenAPI specification model."""

    __tablename__ = "openapi_specs"

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
    spec_content: Mapped[dict] = mapped_column(JSONB, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    git_commit_hash: Mapped[str | None] = mapped_column(String(40), nullable=True, index=True)

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="openapi_specs")

    def __repr__(self) -> str:
        return f"<OpenAPISpec(id={self.id}, project_id={self.project_id}, version={self.version})>"

