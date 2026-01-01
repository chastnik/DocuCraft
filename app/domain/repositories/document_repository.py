"""Document repository interface."""

from abc import abstractmethod
from app.domain.repositories.base import BaseRepository
from app.domain.models.document import DocumentCreate, DocumentUpdate
from app.infrastructure.database.models.document import Document, DocumentVersion


class DocumentRepository(BaseRepository[Document]):
    """Document repository interface."""

    @abstractmethod
    async def get_by_project(self, project_id: str) -> list[Document]:
        """Get documents by project ID."""
        pass

    @abstractmethod
    async def get_by_slug(self, project_id: str, slug: str) -> Document | None:
        """Get document by project ID and slug."""
        pass

    @abstractmethod
    async def create(self, document_data: DocumentCreate, user_id: str) -> Document:
        """Create document."""
        pass

    @abstractmethod
    async def update(
        self,
        document_id: str,
        document_data: DocumentUpdate,
        user_id: str,
    ) -> Document:
        """Update document."""
        pass

    @abstractmethod
    async def create_version(
        self,
        document_id: str,
        content: str,
        content_json: dict | None,
        git_commit_hash: str | None,
        user_id: str | None,
        change_summary: str | None,
    ) -> DocumentVersion:
        """Create document version."""
        pass

    @abstractmethod
    async def get_versions(self, document_id: str) -> list[DocumentVersion]:
        """Get document versions."""
        pass

    @abstractmethod
    async def get_version(self, document_id: str, version_number: int) -> DocumentVersion | None:
        """Get specific document version."""
        pass

