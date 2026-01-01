"""Base AI provider interface."""

from abc import ABC, abstractmethod
from typing import Any


class AIProvider(ABC):
    """Base interface for AI providers."""

    @abstractmethod
    async def analyze_code_changes(
        self,
        diff: str,
        commit_message: str,
        files_changed: list[str],
    ) -> dict[str, Any]:
        """Analyze code changes and suggest documentation updates."""
        pass

    @abstractmethod
    async def generate_documentation_suggestion(
        self,
        document_content: str,
        code_changes: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Generate suggestion for documentation update."""
        pass

    @abstractmethod
    async def suggest_sections_to_update(
        self,
        document_content: str,
        code_changes: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Suggest which sections of documentation need updates."""
        pass

