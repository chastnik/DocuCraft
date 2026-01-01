"""AI Configuration repository interface."""

from abc import abstractmethod
from app.domain.repositories.base import BaseRepository
from app.infrastructure.database.models.ai_configuration import AIConfiguration
from app.domain.models.ai_configuration import AIConfigurationCreate, AIConfigurationUpdate


class AIConfigurationRepository(BaseRepository[AIConfiguration]):
    """AI Configuration repository interface."""

    @abstractmethod
    async def get_by_provider(self, provider: str) -> AIConfiguration | None:
        """Get configuration by provider name."""
        pass

    @abstractmethod
    async def get_active_provider(self) -> AIConfiguration | None:
        """Get active AI provider configuration."""
        pass

    @abstractmethod
    async def get_all(self) -> list[AIConfiguration]:
        """Get all configurations."""
        pass

    @abstractmethod
    async def create(self, config_data: AIConfigurationCreate) -> AIConfiguration:
        """Create AI configuration."""
        pass

    @abstractmethod
    async def update(self, config_id: str, config_data: AIConfigurationUpdate) -> AIConfiguration:
        """Update AI configuration."""
        pass

    @abstractmethod
    async def update_by_provider(
        self, provider: str, config_data: AIConfigurationUpdate
    ) -> AIConfiguration:
        """Update configuration by provider name."""
        pass

