"""Project repository implementation."""

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.repositories.project_repository import ProjectRepository
from app.domain.models.project import ProjectCreate, ProjectUpdate
from app.infrastructure.database.models.project import Project, ProjectMember, ProjectRole
from app.core.exceptions import NotFoundError, ConflictError


class ProjectRepositoryImpl(ProjectRepository):
    """Project repository implementation."""

    async def get_by_id(self, project_id: str) -> Project | None:
        """Get project by ID."""
        result = await self.session.execute(select(Project).where(Project.id == project_id))
        return result.scalar_one_or_none()

    async def get_by_owner(self, owner_id: str) -> list[Project]:
        """Get projects by owner ID."""
        result = await self.session.execute(
            select(Project).where(Project.owner_id == owner_id).order_by(Project.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_user_projects(self, user_id: str) -> list[Project]:
        """Get all projects where user is member or owner."""
        # Get projects where user is owner
        owner_result = await self.session.execute(
            select(Project).where(Project.owner_id == user_id)
        )
        owner_projects = list(owner_result.scalars().all())
        
        # Get projects where user is member
        member_result = await self.session.execute(
            select(Project)
            .join(ProjectMember)
            .where(ProjectMember.user_id == user_id)
        )
        member_projects = list(member_result.scalars().all())
        
        # Combine and remove duplicates
        all_projects = {p.id: p for p in owner_projects + member_projects}
        return sorted(all_projects.values(), key=lambda p: p.created_at, reverse=True)

    async def create(self, project_data: ProjectCreate, owner_id: str) -> Project:
        """Create project."""
        project = Project(
            name=project_data.name,
            description=project_data.description,
            github_repo_url=project_data.github_repo_url,
            ai_mode=project_data.ai_mode,
            owner_id=owner_id,
        )
        self.session.add(project)
        await self.session.commit()
        await self.session.refresh(project)
        return project

    async def update(self, project_id: str, project_data: ProjectUpdate) -> Project:
        """Update project."""
        project = await self.get_by_id(project_id)
        if not project:
            raise NotFoundError("Project")

        if project_data.name is not None:
            project.name = project_data.name
        if project_data.description is not None:
            project.description = project_data.description
        if project_data.github_repo_url is not None:
            project.github_repo_url = project_data.github_repo_url
        if project_data.ai_mode is not None:
            project.ai_mode = project_data.ai_mode

        await self.session.commit()
        await self.session.refresh(project)
        return project

    async def delete(self, project_id: str) -> bool:
        """Delete project."""
        project = await self.get_by_id(project_id)
        if not project:
            return False

        await self.session.delete(project)
        await self.session.commit()
        return True

    async def add_member(
        self,
        project_id: str,
        user_id: str,
        role: str,
    ) -> ProjectMember:
        """Add member to project."""
        # Check if project exists
        project = await self.get_by_id(project_id)
        if not project:
            raise NotFoundError("Project")

        # Check if member already exists
        existing = await self.get_member(project_id, user_id)
        if existing:
            raise ConflictError("User is already a member of this project")

        # Create member
        member = ProjectMember(
            project_id=project_id,
            user_id=user_id,
            role=ProjectRole(role),
        )
        self.session.add(member)
        await self.session.commit()
        await self.session.refresh(member)
        return member

    async def get_member(self, project_id: str, user_id: str) -> ProjectMember | None:
        """Get project member."""
        result = await self.session.execute(
            select(ProjectMember).where(
                and_(ProjectMember.project_id == project_id, ProjectMember.user_id == user_id)
            )
        )
        return result.scalar_one_or_none()

    async def update_member_role(
        self,
        project_id: str,
        user_id: str,
        role: str,
    ) -> ProjectMember:
        """Update member role."""
        member = await self.get_member(project_id, user_id)
        if not member:
            raise NotFoundError("Project member")

        member.role = ProjectRole(role)
        await self.session.commit()
        await self.session.refresh(member)
        return member

    async def remove_member(self, project_id: str, user_id: str) -> bool:
        """Remove member from project."""
        member = await self.get_member(project_id, user_id)
        if not member:
            return False

        await self.session.delete(member)
        await self.session.commit()
        return True

    async def get_members(self, project_id: str) -> list[ProjectMember]:
        """Get all project members."""
        result = await self.session.execute(
            select(ProjectMember).where(ProjectMember.project_id == project_id)
        )
        return list(result.scalars().all())

