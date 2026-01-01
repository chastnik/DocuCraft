"""Git service for analyzing changes."""

from typing import Any
from app.domain.repositories.project_repository import ProjectRepository
from app.domain.repositories.document_repository import DocumentRepository
from app.infrastructure.external.github.client import GitHubClient
from app.core.exceptions import NotFoundError
import re


class GitService:
    """Git service for analyzing code changes."""

    def __init__(
        self,
        project_repository: ProjectRepository,
        document_repository: DocumentRepository,
    ):
        """Initialize git service."""
        self.project_repository = project_repository
        self.document_repository = document_repository

    async def analyze_commit_changes(
        self,
        project_id: str,
        commit_hash: str,
        access_token: str | None = None,
    ) -> dict[str, Any]:
        """Analyze changes in a commit."""
        project = await self.project_repository.get_by_id(project_id)
        if not project:
            raise NotFoundError("Project")

        if not project.github_repo_url:
            raise ValueError("Project does not have GitHub repository configured")

        # Parse repo URL
        github_client = GitHubClient(access_token=access_token)
        repo_info = github_client.parse_repo_url(project.github_repo_url)
        if not repo_info:
            raise ValueError("Invalid GitHub repository URL")

        owner, repo = repo_info

        # Get commit information
        commit = await github_client.get_commit(owner, repo, commit_hash)
        commit_diff = await github_client.get_commit_diff(owner, repo, commit_hash)

        # Analyze diff
        files_changed = self._extract_files_from_diff(commit_diff)
        code_changes = self._analyze_code_changes(commit_diff)

        # Check which documents might be affected
        affected_documents = await self._find_affected_documents(project_id, files_changed)

        return {
            "commit_hash": commit_hash,
            "message": commit.get("commit", {}).get("message", ""),
            "author": commit.get("commit", {}).get("author", {}).get("name", ""),
            "files_changed": files_changed,
            "code_changes": code_changes,
            "affected_documents": affected_documents,
        }

    async def analyze_push_event(
        self,
        project_id: str,
        branch: str,
        commit_hash: str,
        access_token: str | None = None,
    ) -> dict[str, Any]:
        """Analyze push event."""
        project = await self.project_repository.get_by_id(project_id)
        if not project:
            raise NotFoundError("Project")

        if not project.github_repo_url:
            raise ValueError("Project does not have GitHub repository configured")

        github_client = GitHubClient(access_token=access_token)
        repo_info = github_client.parse_repo_url(project.github_repo_url)
        if not repo_info:
            raise ValueError("Invalid GitHub repository URL")

        owner, repo = repo_info

        # Get commit
        commit = await github_client.get_commit(owner, repo, commit_hash)
        commit_diff = await github_client.get_commit_diff(owner, repo, commit_hash)

        files_changed = self._extract_files_from_diff(commit_diff)
        code_changes = self._analyze_code_changes(commit_diff)
        affected_documents = await self._find_affected_documents(project_id, files_changed)

        return {
            "branch": branch,
            "commit_hash": commit_hash,
            "message": commit.get("commit", {}).get("message", ""),
            "files_changed": files_changed,
            "code_changes": code_changes,
            "affected_documents": affected_documents,
        }

    def _extract_files_from_diff(self, diff: str) -> list[str]:
        """Extract changed files from diff."""
        files = []
        for line in diff.split("\n"):
            if line.startswith("diff --git"):
                # Extract file path
                match = re.search(r"diff --git a/(.+?) b/(.+?)$", line)
                if match:
                    files.append(match.group(2))
            elif line.startswith("+++ b/"):
                # Alternative format
                file_path = line.replace("+++ b/", "").strip()
                if file_path and file_path not in files:
                    files.append(file_path)

        return list(set(files))

    def _analyze_code_changes(self, diff: str) -> dict[str, Any]:
        """Analyze code changes in diff."""
        added_lines = 0
        removed_lines = 0
        functions_changed = []
        classes_changed = []

        current_file = None
        for line in diff.split("\n"):
            if line.startswith("+++ b/"):
                current_file = line.replace("+++ b/", "").strip()
            elif line.startswith("@@"):
                # Parse hunk header
                match = re.search(r"@@ -(\d+),?\d* \+(\d+),?\d* @@", line)
                if match:
                    # Extract function/class name if available
                    context = line.split("@@")[-1].strip()
                    if context:
                        if "def " in context or "function" in context.lower():
                            functions_changed.append(context)
                        elif "class " in context:
                            classes_changed.append(context)
            elif line.startswith("+") and not line.startswith("++"):
                added_lines += 1
            elif line.startswith("-") and not line.startswith("--"):
                removed_lines += 1

        return {
            "added_lines": added_lines,
            "removed_lines": removed_lines,
            "functions_changed": list(set(functions_changed)),
            "classes_changed": list(set(classes_changed)),
        }

    async def _find_affected_documents(
        self, project_id: str, files_changed: list[str]
    ) -> list[dict[str, Any]]:
        """Find documents that might be affected by code changes."""
        # Get all documents in project
        documents = await self.document_repository.get_by_project(project_id)

        affected = []
        for doc in documents:
            # Simple heuristic: check if file paths match document title/slug
            doc_lower = doc.title.lower()
            for file_path in files_changed:
                file_name = file_path.split("/")[-1].lower().replace(".py", "").replace(".js", "")
                if file_name in doc_lower or doc_lower in file_name:
                    affected.append(
                        {
                            "document_id": doc.id,
                            "title": doc.title,
                            "slug": doc.slug,
                            "reason": f"File {file_path} might be related",
                        }
                    )
                    break

        return affected

