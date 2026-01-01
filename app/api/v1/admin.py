"""Admin API endpoints for system configuration."""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db
from app.api.v1.auth import get_current_user
from app.domain.models.user import User
from app.domain.models.ai_configuration import (
    AIConfigurationCreate,
    AIConfigurationUpdate,
    AIConfigurationResponse,
)
from app.domain.repositories.ai_configuration_repository import AIConfigurationRepository
from app.infrastructure.database.repositories.ai_configuration_repository_impl import (
    AIConfigurationRepositoryImpl,
)

router = APIRouter()


async def get_ai_config_repository(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AIConfigurationRepository:
    """Get AI configuration repository."""
    return AIConfigurationRepositoryImpl(db)


async def require_superuser(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Require superuser access."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superuser access required",
        )
    return current_user


@router.get("/ai-config", response_model=list[AIConfigurationResponse])
async def get_all_ai_configurations(
    current_user: Annotated[User, Depends(require_superuser)],
    config_repo: Annotated[AIConfigurationRepository, Depends(get_ai_config_repository)],
):
    """Get all AI configurations (admin only)."""
    configs = await config_repo.get_all()
    return [
        AIConfigurationResponse(
            id=config.id,
            provider=config.provider,
            is_active=config.is_active,
            created_at=config.created_at,
            updated_at=config.updated_at,
            api_key_masked=f"***{config.api_key[-4:]}" if len(config.api_key) > 4 else "****",
        )
        for config in configs
    ]


@router.get("/ai-config/{provider}", response_model=AIConfigurationResponse)
async def get_ai_configuration(
    provider: str,
    current_user: Annotated[User, Depends(require_superuser)],
    config_repo: Annotated[AIConfigurationRepository, Depends(get_ai_config_repository)],
):
    """Get AI configuration by provider (admin only)."""
    config = await config_repo.get_by_provider(provider)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Configuration for provider '{provider}' not found",
        )
    return AIConfigurationResponse(
        id=config.id,
        provider=config.provider,
        is_active=config.is_active,
        created_at=config.created_at,
        updated_at=config.updated_at,
        api_key_masked=f"***{config.api_key[-4:]}" if len(config.api_key) > 4 else "****",
    )


@router.post("/ai-config", response_model=AIConfigurationResponse, status_code=status.HTTP_201_CREATED)
async def create_ai_configuration(
    config_data: AIConfigurationCreate,
    current_user: Annotated[User, Depends(require_superuser)],
    config_repo: Annotated[AIConfigurationRepository, Depends(get_ai_config_repository)],
):
    """Create AI configuration (admin only)."""
    try:
        config = await config_repo.create(config_data)
        return AIConfigurationResponse(
            id=config.id,
            provider=config.provider,
            is_active=config.is_active,
            created_at=config.created_at,
            updated_at=config.updated_at,
            api_key_masked=f"***{config.api_key[-4:]}" if len(config.api_key) > 4 else "****",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.put("/ai-config/{provider}", response_model=AIConfigurationResponse)
async def update_ai_configuration(
    provider: str,
    config_data: AIConfigurationUpdate,
    current_user: Annotated[User, Depends(require_superuser)],
    config_repo: Annotated[AIConfigurationRepository, Depends(get_ai_config_repository)],
):
    """Update AI configuration by provider (admin only)."""
    try:
        config = await config_repo.update_by_provider(provider, config_data)
        return AIConfigurationResponse(
            id=config.id,
            provider=config.provider,
            is_active=config.is_active,
            created_at=config.created_at,
            updated_at=config.updated_at,
            api_key_masked=f"***{config.api_key[-4:]}" if len(config.api_key) > 4 else "****",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e),
            )
        raise


@router.delete("/ai-config/{provider}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ai_configuration(
    provider: str,
    current_user: Annotated[User, Depends(require_superuser)],
    config_repo: Annotated[AIConfigurationRepository, Depends(get_ai_config_repository)],
):
    """Delete AI configuration by provider (admin only)."""
    config = await config_repo.get_by_provider(provider)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Configuration for provider '{provider}' not found",
        )
    await config_repo.delete(config.id)

