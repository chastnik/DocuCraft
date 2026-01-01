"""User repository interface."""

from abc import abstractmethod
from app.domain.repositories.base import BaseRepository
from app.domain.models.user import UserCreate, UserUpdate
from app.infrastructure.database.models.user import User


class UserRepository(BaseRepository[User]):
    """User repository interface."""

    @abstractmethod
    async def get_by_email(self, email: str) -> User | None:
        """Get user by email."""
        pass

    @abstractmethod
    async def get_by_username(self, username: str) -> User | None:
        """Get user by username."""
        pass

    @abstractmethod
    async def create(self, user_data: UserCreate, hashed_password: str) -> User:
        """Create user."""
        pass

    @abstractmethod
    async def update(self, user_id: str, user_data: UserUpdate) -> User:
        """Update user."""
        pass

