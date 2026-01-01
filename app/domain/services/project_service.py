"""Project service."""

from app.domain.repositories.project_repository import ProjectRepository
from app.domain.repositories.user_repository import UserRepository
from app.domain.models.project import ProjectCreate, ProjectUpdate, Project, ProjectMember, ProjectMemberCreate, ProjectMemberUpdate
from app.core.exceptions import NotFoundError, ForbiddenError
from app.infrastructure.database.models.project import ProjectRole


class ProjectService:
    """Project service."""

    def __init__(
        self,
        project_repository: ProjectRepository,
        user_repository: UserRepository,
    ):
        """Initialize project service."""
        self.project_repository = project_repository
        self.user_repository = user_repository

    async def create_project(self, project_data: ProjectCreate, owner_id: str) -> Project:
        """Create a new project."""
        project = await self.project_repository.create(project_data, owner_id)
        return Project.model_validate(project)

    async def get_project(self, project_id: str, user_id: str) -> Project:
        """Get project by ID (with access check)."""
        project = await self.project_repository.get_by_id(project_id)
        if not project:
            raise NotFoundError("Project")

        # Check access
        await self._check_access(project_id, user_id)
        return Project.model_validate(project)

    async def list_user_projects(self, user_id: str) -> list[Project]:
        """List all projects for user."""
        projects = await self.project_repository.get_user_projects(user_id)
        return [Project.model_validate(p) for p in projects]

    async def update_project(
        self,
        project_id: str,
        project_data: ProjectUpdate,
        user_id: str,
    ) -> Project:
        """Update project."""
        project = await self.project_repository.get_by_id(project_id)
        if not project:
            raise NotFoundError("Project")

        # Check if user is owner or admin
        await self._check_admin_access(project_id, user_id)

        updated_project = await self.project_repository.update(project_id, project_data)
        return Project.model_validate(updated_project)

    async def delete_project(self, project_id: str, user_id: str) -> bool:
        """Delete project."""
        project = await self.project_repository.get_by_id(project_id)
        if not project:
            raise NotFoundError("Project")

        # Only owner can delete
        if project.owner_id != user_id:
            raise ForbiddenError("Only project owner can delete the project")

        return await self.project_repository.delete(project_id)

    async def add_member(
        self,
        project_id: str,
        member_data: ProjectMemberCreate,
        user_id: str,
    ) -> ProjectMember:
        """Add member to project."""
        # Check access
        await self._check_admin_access(project_id, user_id)

        # Verify user exists
        user = await self.user_repository.get_by_id(member_data.user_id)
        if not user:
            raise NotFoundError("User")

        member = await self.project_repository.add_member(
            project_id,
            member_data.user_id,
            member_data.role,
        )
        return ProjectMember.model_validate(member)

    async def update_member(
        self,
        project_id: str,
        user_id_to_update: str,
        member_data: ProjectMemberUpdate,
        current_user_id: str,
    ) -> ProjectMember:
        """Update project member."""
        # Check access
        await self._check_admin_access(project_id, current_user_id)

        if member_data.role is None:
            raise ValueError("Role is required")

        member = await self.project_repository.update_member_role(
            project_id,
            user_id_to_update,
            member_data.role,
        )
        return ProjectMember.model_validate(member)

    async def remove_member(
        self,
        project_id: str,
        user_id_to_remove: str,
        current_user_id: str,
    ) -> bool:
        """Remove member from project."""
        # Check access
        await self._check_admin_access(project_id, current_user_id)

        return await self.project_repository.remove_member(project_id, user_id_to_remove)

    async def get_members(self, project_id: str, user_id: str) -> list[ProjectMember]:
        """Get project members."""
        # Check access
        await self._check_access(project_id, user_id)

        members = await self.project_repository.get_members(project_id)
        return [ProjectMember.model_validate(m) for m in members]

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

    async def _check_admin_access(self, project_id: str, user_id: str) -> None:
        """Check if user has admin access to project."""
        project = await self.project_repository.get_by_id(project_id)
        if not project:
            raise NotFoundError("Project")

        # Owner has admin access
        if project.owner_id == user_id:
            return

        # Check if user is admin or project lead
        member = await self.project_repository.get_member(project_id, user_id)
        if not member:
            raise ForbiddenError("You don't have access to this project")

        if member.role not in [ProjectRole.ADMIN, ProjectRole.PROJECT_LEAD]:
            raise ForbiddenError("Insufficient permissions")

