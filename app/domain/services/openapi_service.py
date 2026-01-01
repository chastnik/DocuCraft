"""OpenAPI service for parsing and managing API specifications."""

from typing import Any
import json
from app.domain.repositories.project_repository import ProjectRepository
from app.infrastructure.database.models.openapi_spec import OpenAPISpec
from app.core.exceptions import NotFoundError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select


class OpenAPIService:
    """Service for managing OpenAPI specifications."""

    def __init__(
        self,
        project_repository: ProjectRepository,
        db: AsyncSession,
    ):
        """Initialize OpenAPI service."""
        self.project_repository = project_repository
        self.db = db

    async def save_spec(
        self,
        project_id: str,
        spec_content: dict[str, Any],
        git_commit_hash: str | None = None,
    ) -> OpenAPISpec:
        """Save or update OpenAPI specification."""
        project = await self.project_repository.get_by_id(project_id)
        if not project:
            raise NotFoundError("Project")

        # Check if spec already exists
        result = await self.db.execute(
            select(OpenAPISpec)
            .where(OpenAPISpec.project_id == project_id)
            .order_by(OpenAPISpec.version.desc())
        )
        existing_spec = result.scalar_one_or_none()

        if existing_spec:
            # Update existing spec
            existing_spec.spec_content = spec_content
            existing_spec.version += 1
            existing_spec.git_commit_hash = git_commit_hash
            await self.db.commit()
            await self.db.refresh(existing_spec)
            return existing_spec
        else:
            # Create new spec
            new_spec = OpenAPISpec(
                project_id=project_id,
                spec_content=spec_content,
                version=1,
                git_commit_hash=git_commit_hash,
            )
            self.db.add(new_spec)
            await self.db.commit()
            await self.db.refresh(new_spec)
            return new_spec

    async def get_spec(self, project_id: str) -> OpenAPISpec | None:
        """Get latest OpenAPI specification for project."""
        result = await self.db.execute(
            select(OpenAPISpec)
            .where(OpenAPISpec.project_id == project_id)
            .order_by(OpenAPISpec.version.desc())
        )
        return result.scalar_one_or_none()

    async def parse_spec_from_file(self, file_content: str) -> dict[str, Any]:
        """Parse OpenAPI specification from file content."""
        try:
            return json.loads(file_content)
        except json.JSONDecodeError:
            # Try YAML (would need pyyaml)
            raise ValueError("Invalid JSON format. YAML support not implemented yet.")

    async def extract_endpoints(self, spec: dict[str, Any]) -> list[dict[str, Any]]:
        """Extract API endpoints from OpenAPI specification."""
        endpoints = []
        paths = spec.get("paths", {})

        for path, methods in paths.items():
            for method, details in methods.items():
                if method.lower() in ["get", "post", "put", "delete", "patch"]:
                    endpoints.append(
                        {
                            "path": path,
                            "method": method.upper(),
                            "summary": details.get("summary", ""),
                            "description": details.get("description", ""),
                            "operation_id": details.get("operationId", ""),
                            "tags": details.get("tags", []),
                            "parameters": details.get("parameters", []),
                            "responses": details.get("responses", {}),
                        }
                    )

        return endpoints

    async def generate_documentation_sections(
        self, spec: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Generate documentation sections from OpenAPI spec."""
        endpoints = await self.extract_endpoints(spec)
        info = spec.get("info", {})
        tags = spec.get("tags", [])

        sections = []

        # API Overview
        sections.append(
            {
                "title": "API Overview",
                "content": f"""# {info.get('title', 'API')}

{info.get('description', '')}

**Version:** {info.get('version', '1.0.0')}

**Base URL:** {spec.get('servers', [{}])[0].get('url', 'N/A') if spec.get('servers') else 'N/A'}
""",
            }
        )

        # Endpoints by tag
        endpoints_by_tag: dict[str, list] = {}
        for endpoint in endpoints:
            for tag in endpoint.get("tags", ["default"]):
                if tag not in endpoints_by_tag:
                    endpoints_by_tag[tag] = []
                endpoints_by_tag[tag].append(endpoint)

        for tag, tag_endpoints in endpoints_by_tag.items():
            tag_info = next((t for t in tags if t.get("name") == tag), {})
            content = f"## {tag_info.get('description', tag)}\n\n"
            content += tag_info.get("description", "") + "\n\n" if tag_info.get("description") else ""

            for endpoint in tag_endpoints:
                content += f"### {endpoint['method']} {endpoint['path']}\n\n"
                content += f"{endpoint.get('summary', '')}\n\n"
                if endpoint.get("description"):
                    content += f"{endpoint['description']}\n\n"

                # Parameters
                if endpoint.get("parameters"):
                    content += "**Parameters:**\n\n"
                    for param in endpoint["parameters"]:
                        content += f"- `{param.get('name')}` ({param.get('in')}): {param.get('description', '')}\n"
                    content += "\n"

                # Responses
                if endpoint.get("responses"):
                    content += "**Responses:**\n\n"
                    for status_code, response in endpoint["responses"].items():
                        content += f"- `{status_code}`: {response.get('description', '')}\n"
                    content += "\n"

            sections.append({"title": tag, "content": content})

        return sections

    async def link_endpoints_to_documentation(
        self,
        project_id: str,
        document_id: str,
        spec: dict[str, Any],
    ) -> dict[str, Any]:
        """Link API endpoints to documentation sections."""
        endpoints = await self.extract_endpoints(spec)

        # Get document
        from app.infrastructure.database.repositories.document_repository_impl import (
            DocumentRepositoryImpl,
        )
        from app.api.deps import get_db

        async for db in get_db():
            document_repo = DocumentRepositoryImpl(db)
            document = await document_repo.get_by_id(document_id)
            if not document:
                raise NotFoundError("Document")

            # Simple matching: check if endpoint paths/descriptions appear in document
            links = []
            doc_content_lower = document.content.lower()

            for endpoint in endpoints:
                endpoint_text = f"{endpoint['method']} {endpoint['path']}".lower()
                if endpoint_text in doc_content_lower or endpoint.get("summary", "").lower() in doc_content_lower:
                    links.append(
                        {
                            "endpoint": f"{endpoint['method']} {endpoint['path']}",
                            "document_section": "Found in document",
                            "confidence": "high",
                        }
                    )

            return {"links": links}

