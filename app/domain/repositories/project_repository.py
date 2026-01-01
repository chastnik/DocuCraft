"""Project repository interface."""

from abc import abstractmethod
from app.domain.repositories.base import BaseRepository
from app.domain.models.project import ProjectCreate, ProjectUpdate
from app.infrastructure.database.models.project import Project, ProjectMember
from app.infrastructure.database.models.user import User


class ProjectRepository(BaseRepository[Project]):
    """Project repository interface."""

    @abstractmethod
    async def get_by_owner(self, owner_id: str) -> list[Project]:
        """Get projects by owner ID."""
        pass

    @abstractmethod
    async def get_user_projects(self, user_id: str) -> list[Project]:
        """Get all projects where user is member or owner."""
        pass

    @abstractmethod
    async def create(self, project_data: ProjectCreate, owner_id: str) -> Project:
        """Create project."""
        pass

    @abstractmethod
    async def update(self, project_id: str, project_data: ProjectUpdate) -> Project:
        """Update project."""
        pass

    @abstractmethod
    async def add_member(
        self,
        project_id: str,
        user_id: str,
        role: str,
    ) -> ProjectMember:
        """Add member to project."""
        pass

    @abstractmethod
    async def get_member(self, project_id: str, user_id: str) -> ProjectMember | None:
        """Get project member."""
        pass

    @abstractmethod
    async def update_member_role(
        self,
        project_id: str,
        user_id: str,
        role: str,
    ) -> ProjectMember:
        """Update member role."""
        pass

    @abstractmethod
    async def remove_member(self, project_id: str, user_id: str) -> bool:
        """Remove member from project."""
        pass

    @abstractmethod
    async def get_members(self, project_id: str) -> list[ProjectMember]:
        """Get all project members."""
        pass

