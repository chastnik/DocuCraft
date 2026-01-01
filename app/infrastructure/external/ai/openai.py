"""OpenAI AI provider implementation."""

from typing import Any
from openai import AsyncOpenAI
from app.infrastructure.external.ai.base import AIProvider
from app.core.config import settings


class OpenAIProvider(AIProvider):
    """OpenAI provider implementation."""

    def __init__(self):
        """Initialize OpenAI provider."""
        if not settings.openai_api_key:
            raise ValueError("OpenAI API key not configured")
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = "gpt-4-turbo-preview"

    async def analyze_code_changes(
        self,
        diff: str,
        commit_message: str,
        files_changed: list[str],
    ) -> dict[str, Any]:
        """Analyze code changes using OpenAI."""
        prompt = f"""Analyze the following code changes and provide insights:

Commit message: {commit_message}
Files changed: {', '.join(files_changed)}

Diff:
{diff[:4000]}  # Limit diff size

Provide a JSON response with:
- summary: Brief summary of changes
- impact: Impact on documentation (high/medium/low)
- affected_areas: List of documentation areas that might need updates
- suggestions: List of specific documentation update suggestions
"""

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a documentation expert. Analyze code changes and suggest documentation updates.",
                },
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
        )

        import json
        return json.loads(response.choices[0].message.content)

    async def generate_documentation_suggestion(
        self,
        document_content: str,
        code_changes: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Generate documentation update suggestion."""
        prompt = f"""Based on the following code changes, suggest updates to the documentation:

Code changes summary: {code_changes.get('summary', 'N/A')}
Affected areas: {', '.join(code_changes.get('affected_areas', []))}

Current documentation:
{document_content[:2000]}

Provide a JSON response with:
- suggested_content: Updated documentation content
- change_type: Type of change (update/add/delete)
- target_section: Section name or identifier
- reasoning: Explanation of why this change is needed
"""

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a technical writer. Suggest documentation updates based on code changes.",
                },
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
        )

        import json
        return json.loads(response.choices[0].message.content)

    async def suggest_sections_to_update(
        self,
        document_content: str,
        code_changes: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Suggest which sections need updates."""
        prompt = f"""Analyze the documentation and code changes to identify sections that need updates:

Code changes: {code_changes.get('summary', 'N/A')}

Documentation:
{document_content[:3000]}

Provide a JSON array with objects containing:
- section_name: Name or identifier of the section
- priority: high/medium/low
- reason: Why this section needs updating
"""

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a documentation expert. Identify sections that need updates.",
                },
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
        )

        import json
        result = json.loads(response.choices[0].message.content)
        return result.get("sections", [])

