"""Base repository interface."""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Any
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar("T")


class BaseRepository(ABC, Generic[T]):
    """Base repository interface."""

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session."""
        self.session = session

    @abstractmethod
    async def get_by_id(self, id: str) -> T | None:
        """Get entity by ID."""
        pass

    @abstractmethod
    async def create(self, entity: Any) -> T:
        """Create entity."""
        pass

    @abstractmethod
    async def update(self, id: str, entity: Any) -> T:
        """Update entity."""
        pass

    @abstractmethod
    async def delete(self, id: str) -> bool:
        """Delete entity."""
        pass

