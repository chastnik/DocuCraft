"""AI service for documentation suggestions."""

from app.infrastructure.external.ai.base import AIProvider
from app.domain.repositories.document_repository import DocumentRepository
from app.domain.repositories.project_repository import ProjectRepository
from app.infrastructure.database.models.ai_suggestion import AISuggestion, SuggestionType, SuggestionStatus
from app.core.exceptions import NotFoundError
from sqlalchemy.ext.asyncio import AsyncSession


class AIService:
    """AI service for generating documentation suggestions."""

    def __init__(
        self,
        ai_provider: AIProvider,
        document_repository: DocumentRepository,
        project_repository: ProjectRepository,
        db: AsyncSession,
    ):
        """Initialize AI service."""
        self.ai_provider = ai_provider
        self.document_repository = document_repository
        self.project_repository = project_repository
        self.db = db

    async def analyze_and_suggest(
        self,
        project_id: str,
        document_id: str,
        diff: str,
        commit_message: str,
        files_changed: list[str],
        git_event_id: str | None = None,
    ) -> list[AISuggestion]:
        """Analyze code changes and generate suggestions for a document."""
        # Get document
        document = await self.document_repository.get_by_id(document_id)
        if not document:
            raise NotFoundError("Document")

        if document.project_id != project_id:
            raise ValueError("Document does not belong to this project")

        # Analyze code changes
        code_analysis = await self.ai_provider.analyze_code_changes(
            diff, commit_message, files_changed
        )

        # Suggest sections to update
        sections = await self.ai_provider.suggest_sections_to_update(
            document.content, code_analysis
        )

        suggestions = []
        for section in sections:
            # Generate suggestion for each section
            suggestion_data = await self.ai_provider.generate_documentation_suggestion(
                document.content,
                code_analysis,
                {"section": section},
            )

            # Create AI suggestion
            suggestion = AISuggestion(
                document_id=document_id,
                git_event_id=git_event_id,
                suggestion_type=SuggestionType(suggestion_data.get("change_type", "update")),
                target_section=section.get("section_name"),
                suggested_content=suggestion_data.get("suggested_content", ""),
                status=SuggestionStatus.PENDING,
            )

            self.db.add(suggestion)
            suggestions.append(suggestion)

        await self.db.commit()

        # Refresh suggestions
        for suggestion in suggestions:
            await self.db.refresh(suggestion)

        return suggestions

    async def approve_suggestion(
        self,
        suggestion_id: str,
        user_id: str,
    ) -> AISuggestion:
        """Approve and apply an AI suggestion."""
        # Get suggestion
        from sqlalchemy import select
        result = await self.db.execute(
            select(AISuggestion).where(AISuggestion.id == suggestion_id)
        )
        suggestion = result.scalar_one_or_none()

        if not suggestion:
            raise NotFoundError("AI suggestion")

        if suggestion.status != SuggestionStatus.PENDING:
            raise ValueError("Suggestion is not pending")

        # Get document
        document = await self.document_repository.get_by_id(suggestion.document_id)
        if not document:
            raise NotFoundError("Document")

        # Apply suggestion
        if suggestion.suggestion_type == SuggestionType.UPDATE:
            # Update document content
            from app.domain.models.document import DocumentUpdate
            update_data = DocumentUpdate(content=suggestion.suggested_content)
            await self.document_repository.update(document.id, update_data, user_id)
        elif suggestion.suggestion_type == SuggestionType.ADD:
            # Append to document
            new_content = document.content + "\n\n" + suggestion.suggested_content
            from app.domain.models.document import DocumentUpdate
            update_data = DocumentUpdate(content=new_content)
            await self.document_repository.update(document.id, update_data, user_id)

        # Update suggestion status
        suggestion.status = SuggestionStatus.APPLIED
        suggestion.reviewed_by_id = user_id
        from datetime import datetime
        suggestion.reviewed_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(suggestion)

        return suggestion

    async def reject_suggestion(
        self,
        suggestion_id: str,
        user_id: str,
    ) -> AISuggestion:
        """Reject an AI suggestion."""
        from sqlalchemy import select
        result = await self.db.execute(
            select(AISuggestion).where(AISuggestion.id == suggestion_id)
        )
        suggestion = result.scalar_one_or_none()

        if not suggestion:
            raise NotFoundError("AI suggestion")

        suggestion.status = SuggestionStatus.REJECTED
        suggestion.reviewed_by_id = user_id
        from datetime import datetime
        suggestion.reviewed_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(suggestion)

        return suggestion

