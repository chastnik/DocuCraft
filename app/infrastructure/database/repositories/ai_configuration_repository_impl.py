"""AI Configuration repository implementation."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.repositories.ai_configuration_repository import AIConfigurationRepository
from app.domain.models.ai_configuration import AIConfigurationCreate, AIConfigurationUpdate
from app.infrastructure.database.models.ai_configuration import AIConfiguration
from app.core.exceptions import NotFoundError


class AIConfigurationRepositoryImpl(AIConfigurationRepository):
    """AI Configuration repository implementation."""

    async def get_by_id(self, config_id: str) -> AIConfiguration | None:
        """Get configuration by ID."""
        result = await self.session.execute(
            select(AIConfiguration).where(AIConfiguration.id == config_id)
        )
        return result.scalar_one_or_none()

    async def get_by_provider(self, provider: str) -> AIConfiguration | None:
        """Get configuration by provider name."""
        result = await self.session.execute(
            select(AIConfiguration).where(AIConfiguration.provider == provider)
        )
        return result.scalar_one_or_none()

    async def get_active_provider(self) -> AIConfiguration | None:
        """Get active AI provider configuration."""
        result = await self.session.execute(
            select(AIConfiguration).where(AIConfiguration.is_active == True)
        )
        return result.scalar_one_or_none()

    async def get_all(self) -> list[AIConfiguration]:
        """Get all configurations."""
        result = await self.session.execute(select(AIConfiguration))
        return list(result.scalars().all())

    async def create(self, config_data: AIConfigurationCreate) -> AIConfiguration:
        """Create AI configuration."""
        # Check if provider already exists
        existing = await self.get_by_provider(config_data.provider)
        if existing:
            raise ValueError(f"Configuration for provider '{config_data.provider}' already exists")

        config = AIConfiguration(
            provider=config_data.provider,
            api_key=config_data.api_key,
            config=config_data.config,
            is_active=config_data.is_active,
        )
        self.session.add(config)
        await self.session.commit()
        await self.session.refresh(config)
        return config

    async def update(self, config_id: str, config_data: AIConfigurationUpdate) -> AIConfiguration:
        """Update AI configuration."""
        config = await self.get_by_id(config_id)
        if not config:
            raise NotFoundError("AI Configuration")

        if config_data.provider is not None:
            # Check if new provider name conflicts with existing
            if config_data.provider != config.provider:
                existing = await self.get_by_provider(config_data.provider)
                if existing and existing.id != config_id:
                    raise ValueError(
                        f"Configuration for provider '{config_data.provider}' already exists"
                    )
            config.provider = config_data.provider

        if config_data.api_key is not None:
            config.api_key = config_data.api_key
        if config_data.config is not None:
            config.config = config_data.config
        if config_data.is_active is not None:
            config.is_active = config_data.is_active

        await self.session.commit()
        await self.session.refresh(config)
        return config

    async def update_by_provider(
        self, provider: str, config_data: AIConfigurationUpdate
    ) -> AIConfiguration:
        """Update configuration by provider name."""
        config = await self.get_by_provider(provider)
        if not config:
            raise NotFoundError(f"AI Configuration for provider '{provider}'")
        return await self.update(config.id, config_data)

    async def delete(self, config_id: str) -> bool:
        """Delete AI configuration."""
        config = await self.get_by_id(config_id)
        if not config:
            return False

        await self.session.delete(config)
        await self.session.commit()
        return True

