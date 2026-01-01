"""AI suggestions API endpoints."""

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Body
from app.domain.services.ai_service import AIService
from app.infrastructure.external.ai.factory import get_ai_provider
from app.domain.repositories.document_repository import DocumentRepository
from app.domain.repositories.project_repository import ProjectRepository
from app.api.deps import get_project_repository, get_db
from app.api.v1.auth import get_current_user
from app.domain.models.user import User
from app.infrastructure.database.repositories.document_repository_impl import DocumentRepositoryImpl
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


async def get_document_repository(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DocumentRepository:
    """Get document repository."""
    return DocumentRepositoryImpl(db)


async def get_ai_service(
    db: Annotated[AsyncSession, Depends(get_db)],
    document_repo: Annotated[DocumentRepository, Depends(get_document_repository)],
    project_repo: Annotated[ProjectRepository, Depends(get_project_repository)],
) -> AIService:
    """Get AI service."""
    from app.domain.services.ai_service import AIService

    ai_provider = await get_ai_provider(db)
    return AIService(ai_provider, document_repo, project_repo, db)


@router.post("/documents/{document_id}/analyze")
async def analyze_document_changes(
    document_id: str,
    diff: Annotated[str, Body()],
    commit_message: Annotated[str, Body()],
    files_changed: Annotated[list[str], Body()],
    project_id: Annotated[str, Body()],
    git_event_id: Annotated[str | None, Body()] = None,
    current_user: Annotated[User, Depends(get_current_user)] = None,
    ai_service: Annotated[AIService, Depends(get_ai_service)] = None,
):
    """Analyze code changes and generate documentation suggestions."""
    suggestions = await ai_service.analyze_and_suggest(
        project_id=project_id,
        document_id=document_id,
        diff=diff,
        commit_message=commit_message,
        files_changed=files_changed,
        git_event_id=git_event_id,
    )

    return {
        "suggestions": [
            {
                "id": s.id,
                "type": s.suggestion_type,
                "target_section": s.target_section,
                "status": s.status,
            }
            for s in suggestions
        ]
    }


@router.post("/suggestions/{suggestion_id}/approve")
async def approve_suggestion(
    suggestion_id: str,
    current_user: Annotated[User, Depends(get_current_user)] = None,
    ai_service: Annotated[AIService, Depends(get_ai_service)] = None,
):
    """Approve and apply an AI suggestion."""
    suggestion = await ai_service.approve_suggestion(suggestion_id, current_user.id)
    return {
        "id": suggestion.id,
        "status": suggestion.status,
        "message": "Suggestion applied successfully",
    }


@router.post("/suggestions/{suggestion_id}/reject")
async def reject_suggestion(
    suggestion_id: str,
    current_user: Annotated[User, Depends(get_current_user)] = None,
    ai_service: Annotated[AIService, Depends(get_ai_service)] = None,
):
    """Reject an AI suggestion."""
    suggestion = await ai_service.reject_suggestion(suggestion_id, current_user.id)
    return {
        "id": suggestion.id,
        "status": suggestion.status,
        "message": "Suggestion rejected",
    }

