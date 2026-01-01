"""OpenAPI integration API endpoints."""

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Body
from app.domain.services.openapi_service import OpenAPIService
from app.domain.repositories.project_repository import ProjectRepository
from app.api.deps import get_project_repository, get_db
from app.api.v1.auth import get_current_user
from app.domain.models.user import User
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


async def get_openapi_service(
    project_repo: Annotated[ProjectRepository, Depends(get_project_repository)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> OpenAPIService:
    """Get OpenAPI service."""
    from app.domain.services.openapi_service import OpenAPIService
    return OpenAPIService(project_repo, db)


@router.post("/projects/{project_id}/spec")
async def upload_openapi_spec(
    project_id: str,
    file: UploadFile = File(...),
    git_commit_hash: Annotated[str | None, Body()] = None,
    current_user: Annotated[User, Depends(get_current_user)] = None,
    openapi_service: Annotated[OpenAPIService, Depends(get_openapi_service)] = None,
):
    """Upload OpenAPI specification file."""
    # Read file content
    content = await file.read()
    file_content = content.decode("utf-8")

    # Parse spec
    try:
        spec_content = await openapi_service.parse_spec_from_file(file_content)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Save spec
    spec = await openapi_service.save_spec(project_id, spec_content, git_commit_hash)

    return {
        "id": spec.id,
        "version": spec.version,
        "message": "OpenAPI specification uploaded successfully",
    }


@router.post("/projects/{project_id}/spec/json")
async def upload_openapi_spec_json(
    project_id: str,
    spec_content: Annotated[dict, Body()],
    git_commit_hash: Annotated[str | None, Body()] = None,
    current_user: Annotated[User, Depends(get_current_user)] = None,
    openapi_service: Annotated[OpenAPIService, Depends(get_openapi_service)] = None,
):
    """Upload OpenAPI specification as JSON."""
    # Save spec
    spec = await openapi_service.save_spec(project_id, spec_content, git_commit_hash)

    return {
        "id": spec.id,
        "version": spec.version,
        "message": "OpenAPI specification uploaded successfully",
    }


@router.get("/projects/{project_id}/spec")
async def get_openapi_spec(
    project_id: str,
    current_user: Annotated[User, Depends(get_current_user)] = None,
    openapi_service: Annotated[OpenAPIService, Depends(get_openapi_service)] = None,
):
    """Get latest OpenAPI specification for project."""
    spec = await openapi_service.get_spec(project_id)
    if not spec:
        raise HTTPException(status_code=404, detail="OpenAPI specification not found")

    return {
        "id": spec.id,
        "version": spec.version,
        "spec_content": spec.spec_content,
        "git_commit_hash": spec.git_commit_hash,
        "created_at": spec.created_at,
        "updated_at": spec.updated_at,
    }


@router.get("/projects/{project_id}/spec/endpoints")
async def get_endpoints(
    project_id: str,
    current_user: Annotated[User, Depends(get_current_user)] = None,
    openapi_service: Annotated[OpenAPIService, Depends(get_openapi_service)] = None,
):
    """Extract endpoints from OpenAPI specification."""
    spec = await openapi_service.get_spec(project_id)
    if not spec:
        raise HTTPException(status_code=404, detail="OpenAPI specification not found")

    endpoints = await openapi_service.extract_endpoints(spec.spec_content)
    return {"endpoints": endpoints}


@router.post("/projects/{project_id}/spec/generate-docs")
async def generate_documentation(
    project_id: str,
    current_user: Annotated[User, Depends(get_current_user)] = None,
    openapi_service: Annotated[OpenAPIService, Depends(get_openapi_service)] = None,
):
    """Generate documentation sections from OpenAPI specification."""
    spec = await openapi_service.get_spec(project_id)
    if not spec:
        raise HTTPException(status_code=404, detail="OpenAPI specification not found")

    sections = await openapi_service.generate_documentation_sections(spec.spec_content)
    return {"sections": sections}


@router.post("/projects/{project_id}/spec/link/{document_id}")
async def link_endpoints_to_documentation(
    project_id: str,
    document_id: str,
    current_user: Annotated[User, Depends(get_current_user)] = None,
    openapi_service: Annotated[OpenAPIService, Depends(get_openapi_service)] = None,
):
    """Link API endpoints to documentation."""
    spec = await openapi_service.get_spec(project_id)
    if not spec:
        raise HTTPException(status_code=404, detail="OpenAPI specification not found")

    links = await openapi_service.link_endpoints_to_documentation(
        project_id, document_id, spec.spec_content
    )
    return links

