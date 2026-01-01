"""Document repository implementation."""

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.repositories.document_repository import DocumentRepository
from app.domain.models.document import DocumentCreate, DocumentUpdate
from app.infrastructure.database.models.document import Document, DocumentVersion
from app.core.exceptions import NotFoundError, ConflictError


class DocumentRepositoryImpl(DocumentRepository):
    """Document repository implementation."""

    async def get_by_id(self, document_id: str) -> Document | None:
        """Get document by ID."""
        result = await self.session.execute(select(Document).where(Document.id == document_id))
        return result.scalar_one_or_none()

    async def get_by_project(self, project_id: str) -> list[Document]:
        """Get documents by project ID."""
        result = await self.session.execute(
            select(Document)
            .where(Document.project_id == project_id)
            .order_by(Document.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_slug(self, project_id: str, slug: str) -> Document | None:
        """Get document by project ID and slug."""
        result = await self.session.execute(
            select(Document).where(
                (Document.project_id == project_id) & (Document.slug == slug)
            )
        )
        return result.scalar_one_or_none()

    async def create(self, document_data: DocumentCreate, user_id: str) -> Document:
        """Create document."""
        # Check if slug already exists in project
        existing = await self.get_by_slug(document_data.project_id, document_data.slug)
        if existing:
            raise ConflictError("Document with this slug already exists in the project")

        document = Document(
            project_id=document_data.project_id,
            title=document_data.title,
            slug=document_data.slug,
            content=document_data.content,
            content_json=document_data.content_json,
            created_by_id=user_id,
            updated_by_id=user_id,
            version=1,
        )
        self.session.add(document)
        await self.session.commit()
        await self.session.refresh(document)

        # Create initial version
        await self.create_version(
            document.id,
            document_data.content,
            document_data.content_json,
            None,
            user_id,
            "Initial version",
        )

        return document

    async def update(
        self,
        document_id: str,
        document_data: DocumentUpdate,
        user_id: str,
    ) -> Document:
        """Update document."""
        document = await self.get_by_id(document_id)
        if not document:
            raise NotFoundError("Document")

        # Check slug uniqueness if slug is being changed
        if document_data.slug is not None and document_data.slug != document.slug:
            existing = await self.get_by_slug(document.project_id, document_data.slug)
            if existing:
                raise ConflictError("Document with this slug already exists in the project")

        # Update fields
        if document_data.title is not None:
            document.title = document_data.title
        if document_data.slug is not None:
            document.slug = document_data.slug
        if document_data.content is not None:
            document.content = document_data.content
        if document_data.content_json is not None:
            document.content_json = document_data.content_json

        document.updated_by_id = user_id
        document.version += 1

        await self.session.commit()
        await self.session.refresh(document)

        # Create new version
        await self.create_version(
            document.id,
            document.content,
            document.content_json,
            document.git_commit_hash,
            user_id,
            f"Updated to version {document.version}",
        )

        return document

    async def delete(self, document_id: str) -> bool:
        """Delete document."""
        document = await self.get_by_id(document_id)
        if not document:
            return False

        await self.session.delete(document)
        await self.session.commit()
        return True

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
        # Get current document version
        document = await self.get_by_id(document_id)
        if not document:
            raise NotFoundError("Document")

        version = DocumentVersion(
            document_id=document_id,
            version_number=document.version,
            content=content,
            content_json=content_json,
            git_commit_hash=git_commit_hash,
            changed_by_id=user_id,
            change_summary=change_summary,
        )
        self.session.add(version)
        await self.session.commit()
        await self.session.refresh(version)
        return version

    async def get_versions(self, document_id: str) -> list[DocumentVersion]:
        """Get document versions."""
        result = await self.session.execute(
            select(DocumentVersion)
            .where(DocumentVersion.document_id == document_id)
            .order_by(DocumentVersion.version_number.desc())
        )
        return list(result.scalars().all())

    async def get_version(self, document_id: str, version_number: int) -> DocumentVersion | None:
        """Get specific document version."""
        result = await self.session.execute(
            select(DocumentVersion).where(
                (DocumentVersion.document_id == document_id)
                & (DocumentVersion.version_number == version_number)
            )
        )
        return result.scalar_one_or_none()

