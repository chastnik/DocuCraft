"""Git analysis tasks."""

from app.tasks.celery_app import celery_app
from app.infrastructure.database.session import SessionLocal
from app.infrastructure.database.models.git_event import GitEvent
from app.domain.services.git_service import GitService
from app.infrastructure.database.repositories.project_repository_impl import ProjectRepositoryImpl
from app.infrastructure.database.repositories.document_repository_impl import DocumentRepositoryImpl
from sqlalchemy.orm import Session


@celery_app.task(name="process_git_event")
def process_git_event(git_event_id: str):
    """Process git event asynchronously."""
    # Use sync session for Celery
    db: Session = next(SessionLocal())
    try:
        git_event = db.query(GitEvent).filter(GitEvent.id == git_event_id).first()
        if not git_event:
            return {"status": "error", "message": "Git event not found"}

        if git_event.processed:
            return {"status": "skipped", "message": "Event already processed"}

        # Create repositories
        project_repo = ProjectRepositoryImpl(db)
        document_repo = DocumentRepositoryImpl(db)

        # Create git service (sync version would be needed)
        # For now, mark as processed
        git_event.processed = True
        db.commit()

        return {
            "status": "success",
            "event_id": git_event_id,
            "message": "Event processed",
        }
    finally:
        db.close()


@celery_app.task(name="analyze_commit_changes")
def analyze_commit_changes(project_id: str, commit_hash: str):
    """Analyze commit changes asynchronously."""
    # This would trigger AI analysis
    return {
        "status": "success",
        "project_id": project_id,
        "commit_hash": commit_hash,
    }

