"""Document service."""

from app.domain.repositories.document_repository import DocumentRepository
from app.domain.repositories.project_repository import ProjectRepository
from app.domain.models.document import (
    DocumentCreate,
    DocumentUpdate,
    Document,
    DocumentVersion,
)
from app.core.exceptions import NotFoundError, ForbiddenError
from app.infrastructure.database.models.project import ProjectRole


class DocumentService:
    """Document service."""

    def __init__(
        self,
        document_repository: DocumentRepository,
        project_repository: ProjectRepository,
    ):
        """Initialize document service."""
        self.document_repository = document_repository
        self.project_repository = project_repository

    async def create_document(
        self,
        document_data: DocumentCreate,
        user_id: str,
    ) -> Document:
        """Create a new document."""
        # Check project access
        await self._check_editor_access(document_data.project_id, user_id)

        document = await self.document_repository.create(document_data, user_id)
        return Document.model_validate(document)

    async def get_document(self, document_id: str, user_id: str) -> Document:
        """Get document by ID."""
        document = await self.document_repository.get_by_id(document_id)
        if not document:
            raise NotFoundError("Document")

        # Check project access
        await self._check_access(document.project_id, user_id)

        return Document.model_validate(document)

    async def list_documents(self, project_id: str, user_id: str) -> list[Document]:
        """List documents in project."""
        # Check project access
        await self._check_access(project_id, user_id)

        documents = await self.document_repository.get_by_project(project_id)
        return [Document.model_validate(d) for d in documents]

    async def update_document(
        self,
        document_id: str,
        document_data: DocumentUpdate,
        user_id: str,
    ) -> Document:
        """Update document."""
        document = await self.document_repository.get_by_id(document_id)
        if not document:
            raise NotFoundError("Document")

        # Check editor access
        await self._check_editor_access(document.project_id, user_id)

        updated_document = await self.document_repository.update(
            document_id, document_data, user_id
        )
        return Document.model_validate(updated_document)

    async def delete_document(self, document_id: str, user_id: str) -> bool:
        """Delete document."""
        document = await self.document_repository.get_by_id(document_id)
        if not document:
            raise NotFoundError("Document")

        # Check editor access
        await self._check_editor_access(document.project_id, user_id)

        return await self.document_repository.delete(document_id)

    async def get_versions(self, document_id: str, user_id: str) -> list[DocumentVersion]:
        """Get document versions."""
        document = await self.document_repository.get_by_id(document_id)
        if not document:
            raise NotFoundError("Document")

        # Check access
        await self._check_access(document.project_id, user_id)

        versions = await self.document_repository.get_versions(document_id)
        return [DocumentVersion.model_validate(v) for v in versions]

    async def get_version(
        self,
        document_id: str,
        version_number: int,
        user_id: str,
    ) -> DocumentVersion:
        """Get specific document version."""
        document = await self.document_repository.get_by_id(document_id)
        if not document:
            raise NotFoundError("Document")

        # Check access
        await self._check_access(document.project_id, user_id)

        version = await self.document_repository.get_version(document_id, version_number)
        if not version:
            raise NotFoundError("Document version")

        return DocumentVersion.model_validate(version)

    async def _check_access(self, project_id: str, user_id: str) -> None:
        """Check if user has access to project."""
        project = await self.project_repository.get_by_id(project_id)
        if not project:
            raise NotFoundError("Project")

        # Owner has access
        if project.owner_id == user_id:
            return

        # Check if user is member
        member = await self.project_repository.get_member(project_id, user_id)
        if not member:
            raise ForbiddenError("You don't have access to this project")

    async def _check_editor_access(self, project_id: str, user_id: str) -> None:
        """Check if user has editor access to project."""
        project = await self.project_repository.get_by_id(project_id)
        if not project:
            raise NotFoundError("Project")

        # Owner has editor access
        if project.owner_id == user_id:
            return

        # Check if user is editor, project lead, or admin
        member = await self.project_repository.get_member(project_id, user_id)
        if not member:
            raise ForbiddenError("You don't have access to this project")

        if member.role not in [
            ProjectRole.EDITOR,
            ProjectRole.PROJECT_LEAD,
            ProjectRole.ADMIN,
        ]:
            raise ForbiddenError("You don't have permission to edit documents")

