"""Git integration API endpoints."""

from typing import Annotated
from fastapi import APIRouter, Depends, Header, HTTPException, status, Request
from app.domain.services.git_service import GitService
from app.domain.repositories.project_repository import ProjectRepository
from app.domain.repositories.document_repository import DocumentRepository
from app.api.deps import get_db
from app.api.deps import get_project_repository, get_user_repository
from app.api.v1.auth import get_current_user
from app.domain.models.user import User
from app.infrastructure.external.github.webhook import verify_webhook_signature, parse_webhook_event
from app.core.config import settings
from app.infrastructure.database.models.git_event import GitEvent
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db
import json

router = APIRouter()


async def get_document_repository_for_git(
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get document repository for git service."""
    from app.infrastructure.database.repositories.document_repository_impl import (
        DocumentRepositoryImpl,
    )
    return DocumentRepositoryImpl(db)


async def get_git_service(
    project_repo: Annotated[ProjectRepository, Depends(get_project_repository)],
    document_repo: Annotated[DocumentRepository, Depends(get_document_repository_for_git)],
) -> GitService:
    """Get git service."""
    from app.domain.services.git_service import GitService
    return GitService(project_repo, document_repo)


@router.post("/webhook/{project_id}")
async def github_webhook(
    project_id: str,
    request: Request,
    x_github_event: Annotated[str | None, Header(alias="X-GitHub-Event")] = None,
    x_hub_signature_256: Annotated[str | None, Header(alias="X-Hub-Signature-256")] = None,
    db: Annotated[AsyncSession, Depends(get_db)],
    project_repo: Annotated[ProjectRepository, Depends(get_project_repository)],
):
    """Handle GitHub webhook events."""
    # Get project
    project = await project_repo.get_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if not project.github_webhook_secret:
        raise HTTPException(status_code=400, detail="Webhook secret not configured")

    # Read payload
    payload_body = await request.body()

    # Verify signature
    if not verify_webhook_signature(payload_body, x_hub_signature_256, project.github_webhook_secret):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    # Parse payload
    payload = json.loads(payload_body.decode("utf-8"))

    # Parse event
    event_info = parse_webhook_event(x_github_event or "unknown", payload)

    # Save event to database
    git_event = GitEvent(
        project_id=project_id,
        event_type=x_github_event or "unknown",
        commit_hash=event_info.get("commit_hash"),
        branch=event_info.get("branch"),
        payload=payload,
        processed=False,
    )
    db.add(git_event)
    await db.commit()
    await db.refresh(git_event)

    # TODO: Trigger Celery task to process the event asynchronously
    # from app.tasks.git_analysis import process_git_event
    # process_git_event.delay(git_event.id)

    return {
        "status": "received",
        "event_id": git_event.id,
        "event_type": x_github_event,
    }


@router.get("/projects/{project_id}/analyze/{commit_hash}")
async def analyze_commit(
    project_id: str,
    commit_hash: str,
    current_user: Annotated[User, Depends(get_current_user)] = None,
    git_service: Annotated[GitService, Depends(get_git_service)] = None,
):
    """Analyze a specific commit."""
    # TODO: Get user's GitHub access token from database
    access_token = None

    result = await git_service.analyze_commit_changes(
        project_id, commit_hash, access_token
    )
    return result


@router.get("/projects/{project_id}/commits")
async def list_commits(
    project_id: str,
    branch: str = "main",
    current_user: Annotated[User, Depends(get_current_user)] = None,
    project_repo: Annotated[ProjectRepository, Depends(get_project_repository)] = None,
):
    """List recent commits for a project."""
    project = await project_repo.get_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if not project.github_repo_url:
        raise HTTPException(status_code=400, detail="GitHub repository not configured")

    from app.infrastructure.external.github.client import GitHubClient

    github_client = GitHubClient()
    repo_info = github_client.parse_repo_url(project.github_repo_url)
    if not repo_info:
        raise HTTPException(status_code=400, detail="Invalid repository URL")

    owner, repo = repo_info
    commits = await github_client.list_commits(owner, repo, branch)

    return {
        "commits": [
            {
                "sha": commit["sha"],
                "message": commit["commit"]["message"],
                "author": commit["commit"]["author"]["name"],
                "date": commit["commit"]["author"]["date"],
            }
            for commit in commits[:20]  # Last 20 commits
        ]
    }

