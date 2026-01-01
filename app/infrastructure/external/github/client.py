"""GitHub API client."""

from typing import Any
import httpx
from app.core.config import settings


class GitHubClient:
    """GitHub API client."""

    BASE_URL = "https://api.github.com"

    def __init__(self, access_token: str | None = None):
        """Initialize GitHub client."""
        self.access_token = access_token
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "DocuCraft/1.0",
        }
        if access_token:
            self.headers["Authorization"] = f"token {access_token}"

    async def get_repo_info(self, owner: str, repo: str) -> dict[str, Any]:
        """Get repository information."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/repos/{owner}/{repo}",
                headers=self.headers,
            )
            response.raise_for_status()
            return response.json()

    async def get_commit(self, owner: str, repo: str, sha: str) -> dict[str, Any]:
        """Get commit information."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/repos/{owner}/{repo}/commits/{sha}",
                headers=self.headers,
            )
            response.raise_for_status()
            return response.json()

    async def get_commit_diff(self, owner: str, repo: str, sha: str) -> str:
        """Get commit diff."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/repos/{owner}/{repo}/commits/{sha}",
                headers={**self.headers, "Accept": "application/vnd.github.v3.diff"},
            )
            response.raise_for_status()
            return response.text

    async def get_compare(self, owner: str, repo: str, base: str, head: str) -> dict[str, Any]:
        """Compare two commits/branches."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/repos/{owner}/{repo}/compare/{base}...{head}",
                headers=self.headers,
            )
            response.raise_for_status()
            return response.json()

    async def get_file_contents(
        self, owner: str, repo: str, path: str, ref: str = "main"
    ) -> dict[str, Any]:
        """Get file contents."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/repos/{owner}/{repo}/contents/{path}",
                headers=self.headers,
                params={"ref": ref},
            )
            response.raise_for_status()
            return response.json()

    async def get_pull_request(self, owner: str, repo: str, pr_number: int) -> dict[str, Any]:
        """Get pull request information."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/repos/{owner}/{repo}/pulls/{pr_number}",
                headers=self.headers,
            )
            response.raise_for_status()
            return response.json()

    async def list_commits(
        self, owner: str, repo: str, sha: str = "main", path: str | None = None
    ) -> list[dict[str, Any]]:
        """List commits."""
        async with httpx.AsyncClient() as client:
            params = {"sha": sha}
            if path:
                params["path"] = path

            response = await client.get(
                f"{self.BASE_URL}/repos/{owner}/{repo}/commits",
                headers=self.headers,
                params=params,
            )
            response.raise_for_status()
            return response.json()

    def parse_repo_url(self, repo_url: str) -> tuple[str, str] | None:
        """Parse GitHub repository URL to owner and repo name."""
        # Support formats:
        # https://github.com/owner/repo
        # https://github.com/owner/repo.git
        # git@github.com:owner/repo.git
        # owner/repo

        if not repo_url:
            return None

        # Remove .git suffix
        repo_url = repo_url.rstrip(".git")

        # Handle git@ format
        if repo_url.startswith("git@github.com:"):
            parts = repo_url.replace("git@github.com:", "").split("/")
            if len(parts) == 2:
                return (parts[0], parts[1])

        # Handle https:// format
        if "github.com" in repo_url:
            parts = repo_url.split("github.com/")[-1].split("/")
            if len(parts) >= 2:
                return (parts[0], parts[1])

        # Handle owner/repo format
        if "/" in repo_url and not repo_url.startswith("http"):
            parts = repo_url.split("/")
            if len(parts) == 2:
                return (parts[0], parts[1])

        return None

