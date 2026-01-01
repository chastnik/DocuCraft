"""Projects API endpoints."""

from typing import Annotated
from fastapi import APIRouter, Depends, status
from app.domain.models.project import (
    Project,
    ProjectCreate,
    ProjectUpdate,
    ProjectMember,
    ProjectMemberCreate,
    ProjectMemberUpdate,
    GitConfiguration,
)
from app.domain.services.project_service import ProjectService
from app.domain.repositories.project_repository import ProjectRepository
from app.domain.repositories.user_repository import UserRepository
from app.api.deps import get_user_repository
from app.api.v1.auth import get_current_user
from app.domain.models.user import User
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db

router = APIRouter()


async def get_project_repository(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ProjectRepository:
    """Get project repository."""
    from app.infrastructure.database.repositories.project_repository_impl import (
        ProjectRepositoryImpl,
    )

    return ProjectRepositoryImpl(db)


async def get_project_service(
    project_repo: Annotated[ProjectRepository, Depends(get_project_repository)],
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
) -> ProjectService:
    """Get project service."""
    return ProjectService(project_repo, user_repo)


@router.get("/", response_model=list[Project])
async def list_projects(
    current_user: Annotated[User, Depends(get_current_user)],
    project_service: Annotated[ProjectService, Depends(get_project_service)],
):
    """List all projects for current user."""
    return await project_service.list_user_projects(current_user.id)


@router.post("/", response_model=Project, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    project_service: Annotated[ProjectService, Depends(get_project_service)],
):
    """Create a new project."""
    return await project_service.create_project(project_data, current_user.id)


@router.get("/{project_id}", response_model=Project)
async def get_project(
    project_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    project_service: Annotated[ProjectService, Depends(get_project_service)],
):
    """Get project by ID."""
    return await project_service.get_project(project_id, current_user.id)


@router.put("/{project_id}", response_model=Project)
async def update_project(
    project_id: str,
    project_data: ProjectUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    project_service: Annotated[ProjectService, Depends(get_project_service)],
):
    """Update project."""
    return await project_service.update_project(project_id, project_data, current_user.id)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    project_service: Annotated[ProjectService, Depends(get_project_service)],
):
    """Delete project."""
    await project_service.delete_project(project_id, current_user.id)
    return None


@router.get("/{project_id}/members", response_model=list[ProjectMember])
async def list_members(
    project_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    project_service: Annotated[ProjectService, Depends(get_project_service)],
):
    """List project members."""
    return await project_service.get_members(project_id, current_user.id)


@router.post("/{project_id}/members", response_model=ProjectMember, status_code=status.HTTP_201_CREATED)
async def add_member(
    project_id: str,
    member_data: ProjectMemberCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    project_service: Annotated[ProjectService, Depends(get_project_service)],
):
    """Add member to project."""
    return await project_service.add_member(project_id, member_data, current_user.id)


@router.put("/{project_id}/members/{user_id}", response_model=ProjectMember)
async def update_member(
    project_id: str,
    user_id: str,
    member_data: ProjectMemberUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    project_service: Annotated[ProjectService, Depends(get_project_service)],
):
    """Update project member role."""
    return await project_service.update_member(
        project_id, user_id, member_data, current_user.id
    )


@router.delete("/{project_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    project_id: str,
    user_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    project_service: Annotated[ProjectService, Depends(get_project_service)],
):
    """Remove member from project."""
    await project_service.remove_member(project_id, user_id, current_user.id)
    return None


@router.get("/{project_id}/git-config", response_model=GitConfiguration)
async def get_git_config(
    project_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    project_service: Annotated[ProjectService, Depends(get_project_service)],
):
    """Get Git configuration for a project."""
    project = await project_service.get_project(project_id, current_user.id)
    return GitConfiguration(
        provider=project.git_provider,
        repo_url=project.git_repo_url,
        api_base_url=project.git_api_base_url,
        webhook_secret=None,  # Never return secret in GET requests
        access_token=None,  # Never return token
    )


@router.put("/{project_id}/git-config", response_model=GitConfiguration)
async def update_git_config(
    project_id: str,
    git_config: GitConfiguration,
    current_user: Annotated[User, Depends(get_current_user)],
    project_service: Annotated[ProjectService, Depends(get_project_service)],
    project_repo: Annotated[ProjectRepository, Depends(get_project_repository)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Update Git configuration for a project."""
    # Verify user has permission to modify project
    project = await project_service.get_project(project_id, current_user.id)
    
    # TODO: Encrypt access_token before storing in database
    # For now, store as-is (should be encrypted in production)
    
    from app.infrastructure.database.models.project import GitProvider
    from fastapi import HTTPException
    
    # Get project model from database
    db_project = await project_repo.get_by_id(project_id)
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Update Git fields (only update provided fields)
    if git_config.provider is not None:
        db_project.git_provider = GitProvider(git_config.provider) if git_config.provider else None
    if git_config.repo_url is not None:
        db_project.git_repo_url = git_config.repo_url
    if git_config.api_base_url is not None:
        db_project.git_api_base_url = git_config.api_base_url
    if git_config.access_token is not None:
        db_project.git_access_token = git_config.access_token
    if git_config.webhook_secret is not None:
        db_project.git_webhook_secret = git_config.webhook_secret
    
    await db.commit()
    await db.refresh(db_project)
    
    return GitConfiguration(
        provider=db_project.git_provider.value if db_project.git_provider else None,
        repo_url=db_project.git_repo_url,
        api_base_url=db_project.git_api_base_url,
        webhook_secret=None,  # Never return secret
        access_token=None,  # Never return token
    )
