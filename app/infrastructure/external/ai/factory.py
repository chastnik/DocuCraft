"""AI provider factory."""

from app.infrastructure.external.ai.base import AIProvider
from app.infrastructure.external.ai.openai import OpenAIProvider
from app.infrastructure.external.ai.anthropic import AnthropicProvider
from app.core.config import settings


def get_ai_provider() -> AIProvider:
    """Get AI provider based on configuration."""
    provider_name = settings.ai_provider.lower()

    if provider_name == "openai":
        return OpenAIProvider()
    elif provider_name == "anthropic":
        return AnthropicProvider()
    else:
        raise ValueError(f"Unknown AI provider: {provider_name}")

