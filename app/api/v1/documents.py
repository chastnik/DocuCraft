"""Documents API endpoints."""

from typing import Annotated
from fastapi import APIRouter, Depends, status, Path, Body
from app.domain.models.document import (
    Document,
    DocumentCreate,
    DocumentUpdate,
    DocumentVersion,
)
from app.domain.services.document_service import DocumentService
from app.domain.repositories.document_repository import DocumentRepository
from app.domain.repositories.project_repository import ProjectRepository
from app.api.deps import get_user_repository
from app.api.v1.auth import get_current_user
from app.domain.models.user import User
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db

router = APIRouter()


async def get_document_repository(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DocumentRepository:
    """Get document repository."""
    from app.infrastructure.database.repositories.document_repository_impl import (
        DocumentRepositoryImpl,
    )

    return DocumentRepositoryImpl(db)


async def get_project_repository(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ProjectRepository:
    """Get project repository."""
    from app.infrastructure.database.repositories.project_repository_impl import (
        ProjectRepositoryImpl,
    )

    return ProjectRepositoryImpl(db)


async def get_document_service(
    document_repo: Annotated[DocumentRepository, Depends(get_document_repository)],
    project_repo: Annotated[ProjectRepository, Depends(get_project_repository)],
) -> DocumentService:
    """Get document service."""
    from app.domain.services.document_service import DocumentService

    return DocumentService(document_repo, project_repo)


@router.get("/projects/{project_id}/documents", response_model=list[Document])
async def list_documents(
    project_id: str = Path(..., description="Project ID"),
    current_user: Annotated[User, Depends(get_current_user)] = None,
    document_service: Annotated[DocumentService, Depends(get_document_service)] = None,
):
    """List documents in project."""
    return await document_service.list_documents(project_id, current_user.id)


@router.post(
    "/projects/{project_id}/documents",
    response_model=Document,
    status_code=status.HTTP_201_CREATED,
)
async def create_document(
    project_id: str = Path(..., description="Project ID"),
    document_data: Annotated[DocumentCreate, Body()] = None,
    current_user: Annotated[User, Depends(get_current_user)] = None,
    document_service: Annotated[DocumentService, Depends(get_document_service)] = None,
):
    """Create a new document."""
    if document_data is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Document data is required")
    document_data.project_id = project_id
    return await document_service.create_document(document_data, current_user.id)


@router.get("/{document_id}", response_model=Document)
async def get_document(
    document_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    document_service: Annotated[DocumentService, Depends(get_document_service)],
):
    """Get document by ID."""
    return await document_service.get_document(document_id, current_user.id)


@router.put("/{document_id}", response_model=Document)
async def update_document(
    document_id: str,
    document_data: DocumentUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    document_service: Annotated[DocumentService, Depends(get_document_service)],
):
    """Update document."""
    return await document_service.update_document(document_id, document_data, current_user.id)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    document_service: Annotated[DocumentService, Depends(get_document_service)],
):
    """Delete document."""
    await document_service.delete_document(document_id, current_user.id)
    return None


@router.get("/{document_id}/versions", response_model=list[DocumentVersion])
async def list_versions(
    document_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    document_service: Annotated[DocumentService, Depends(get_document_service)],
):
    """List document versions."""
    return await document_service.get_versions(document_id, current_user.id)


@router.get("/{document_id}/versions/{version_number}", response_model=DocumentVersion)
async def get_version(
    document_id: str,
    version_number: int,
    current_user: Annotated[User, Depends(get_current_user)],
    document_service: Annotated[DocumentService, Depends(get_document_service)],
):
    """Get specific document version."""
    return await document_service.get_version(document_id, version_number, current_user.id)
