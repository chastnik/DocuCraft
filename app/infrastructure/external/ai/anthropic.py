"""Anthropic AI provider implementation."""

from typing import Any
from anthropic import AsyncAnthropic
from app.infrastructure.external.ai.base import AIProvider
from app.core.config import settings


class AnthropicProvider(AIProvider):
    """Anthropic provider implementation."""

    def __init__(self, api_key: str | None = None):
        """Initialize Anthropic provider."""
        api_key = api_key or settings.anthropic_api_key
        if not api_key:
            raise ValueError("Anthropic API key not configured")
        self.client = AsyncAnthropic(api_key=api_key)
        self.model = "claude-3-opus-20240229"

    async def analyze_code_changes(
        self,
        diff: str,
        commit_message: str,
        files_changed: list[str],
    ) -> dict[str, Any]:
        """Analyze code changes using Anthropic."""
        prompt = f"""Analyze the following code changes and provide insights:

Commit message: {commit_message}
Files changed: {', '.join(files_changed)}

Diff:
{diff[:4000]}

Provide a JSON response with:
- summary: Brief summary of changes
- impact: Impact on documentation (high/medium/low)
- affected_areas: List of documentation areas that might need updates
- suggestions: List of specific documentation update suggestions
"""

        message = await self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        )

        import json
        content = message.content[0].text
        return json.loads(content)

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

        message = await self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        )

        import json
        content = message.content[0].text
        return json.loads(content)

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

        message = await self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        )

        import json
        content = message.content[0].text
        result = json.loads(content)
        return result.get("sections", [])

