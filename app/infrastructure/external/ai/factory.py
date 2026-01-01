"""AI provider factory."""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.external.ai.base import AIProvider
from app.infrastructure.external.ai.openai import OpenAIProvider
from app.infrastructure.external.ai.anthropic import AnthropicProvider
from app.core.config import settings


async def get_ai_provider(db: Optional[AsyncSession] = None) -> AIProvider:
    """Get AI provider based on configuration.
    
    First tries to get configuration from database if db session is provided.
    Falls back to .env settings if database configuration is not available.
    """
    provider_name = settings.ai_provider.lower()
    api_key = None
    
    # Try to get configuration from database
    if db is not None:
        try:
            from app.infrastructure.database.repositories.ai_configuration_repository_impl import (
                AIConfigurationRepositoryImpl,
            )
            config_repo = AIConfigurationRepositoryImpl(db)
            # Try to get active provider first
            config = await config_repo.get_active_provider()
            if config:
                provider_name = config.provider.lower()
                api_key = config.api_key
            else:
                # If no active provider, try to get by configured provider name
                config = await config_repo.get_by_provider(provider_name)
                if config:
                    api_key = config.api_key
        except Exception:
            # If database lookup fails, fall back to .env settings
            pass
    
    # Create provider with API key from DB or .env
    if provider_name == "openai":
        return OpenAIProvider(api_key=api_key)
    elif provider_name == "anthropic":
        return AnthropicProvider(api_key=api_key)
    else:
        raise ValueError(f"Unknown AI provider: {provider_name}")

