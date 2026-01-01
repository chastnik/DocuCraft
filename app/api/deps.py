"""FastAPI dependencies."""

from typing import Annotated
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.database.session import get_async_session
from app.core.security import decode_access_token
from app.core.exceptions import UnauthorizedError
from app.domain.repositories.user_repository import UserRepository
from app.infrastructure.database.repositories.user_repository_impl import UserRepositoryImpl
from app.domain.repositories.project_repository import ProjectRepository
from app.infrastructure.database.repositories.project_repository_impl import ProjectRepositoryImpl
from app.infrastructure.database.models.project import ProjectRole


async def get_db() -> AsyncSession:
    """Get database session."""
    async for session in get_async_session():
        yield session


async def get_user_repository(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserRepository:
    """Get user repository."""
    return UserRepositoryImpl(db)


async def get_project_repository(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ProjectRepository:
    """Get project repository."""
    return ProjectRepositoryImpl(db)


async def get_current_user_id(
    token: str | None = None,
) -> str:
    """Get current user ID from JWT token."""
    if not token:
        raise UnauthorizedError("Not authenticated")
    
    payload = decode_access_token(token)
    if payload is None:
        raise UnauthorizedError("Invalid token")
    
    user_id: str | None = payload.get("sub")
    if user_id is None:
        raise UnauthorizedError("Invalid token payload")
    
    return user_id


def require_role(required_role: ProjectRole):
    """Dependency factory for role-based access control."""
    async def role_checker(
        project_id: str,
        current_user_id: str,
        project_repo: Annotated[ProjectRepository, Depends(get_project_repository)],
    ) -> bool:
        """Check if user has required role."""
        project = await project_repo.get_by_id(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Owner has all permissions
        if project.owner_id == current_user_id:
            return True

        # Check member role
        member = await project_repo.get_member(project_id, current_user_id)
        if not member:
            raise HTTPException(status_code=403, detail="Access denied")

        # Check role hierarchy
        role_hierarchy = {
            ProjectRole.VIEWER: 1,
            ProjectRole.EDITOR: 2,
            ProjectRole.PROJECT_LEAD: 3,
            ProjectRole.ADMIN: 4,
        }

        if role_hierarchy.get(member.role, 0) >= role_hierarchy.get(required_role, 0):
            return True

        raise HTTPException(status_code=403, detail="Insufficient permissions")

    return role_checker
