"""Validation utilities."""

import re
from typing import Any
from pydantic import BaseModel, validator


def validate_slug(slug: str) -> bool:
    """Validate document slug."""
    if not slug:
        return False
    # Allow lowercase letters, numbers, hyphens, underscores
    pattern = r"^[a-z0-9_-]+$"
    return bool(re.match(pattern, slug))


def validate_github_url(url: str) -> bool:
    """Validate GitHub repository URL."""
    if not url:
        return False

    patterns = [
        r"^https://github\.com/[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+(?:\.git)?$",
        r"^git@github\.com:[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+(?:\.git)?$",
        r"^[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+$",
    ]

    return any(re.match(pattern, url) for pattern in patterns)


def validate_git_url(url: str, provider: str | None = None) -> bool:
    """Validate Git repository URL for different providers."""
    if not url:
        return False

    # GitHub
    if provider == "github" or (not provider and "github.com" in url):
        return validate_github_url(url)

    # GitLab
    if provider == "gitlab":
        patterns = [
            r"^https://gitlab\.com/[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+(?:\.git)?$",
            r"^git@gitlab\.com:[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+(?:\.git)?$",
            r"^https://[a-zA-Z0-9.-]+/.*",  # Custom GitLab instance
            r"^git@[a-zA-Z0-9.-]+:.*",  # SSH format for custom GitLab
        ]
        return any(re.match(pattern, url) for pattern in patterns)

    # Gitea
    if provider == "gitea":
        patterns = [
            r"^https://[a-zA-Z0-9.-]+/.*",  # HTTPS
            r"^git@[a-zA-Z0-9.-]+:.*",  # SSH
        ]
        return any(re.match(pattern, url) for pattern in patterns)

    # Custom - accept any valid URL format
    if provider == "custom":
        patterns = [
            r"^https?://[a-zA-Z0-9.-]+(:[0-9]+)?/.*",  # HTTP/HTTPS
            r"^git@[a-zA-Z0-9.-]+(:[0-9]+)?:.*",  # SSH
            r"^ssh://.*",  # SSH URL
        ]
        return any(re.match(pattern, url) for pattern in patterns)

    # Generic validation if provider not specified
    patterns = [
        r"^https?://.*",  # HTTP/HTTPS
        r"^git@.*",  # SSH
        r"^ssh://.*",  # SSH URL
    ]
    return any(re.match(pattern, url) for pattern in patterns)


def validate_commit_hash(commit_hash: str) -> bool:
    """Validate git commit hash."""
    if not commit_hash:
        return False
    # Git commit hashes are 40 characters (SHA-1) or 7+ characters (short)
    pattern = r"^[a-f0-9]{7,40}$"
    return bool(re.match(pattern, commit_hash, re.IGNORECASE))


def sanitize_markdown(content: str) -> str:
    """Basic sanitization of markdown content."""
    # Remove potentially dangerous HTML/scripts
    # In production, use a proper markdown sanitizer like bleach
    return content


class DocumentContentValidator:
    """Validator for document content."""

    MAX_CONTENT_LENGTH = 10_000_000  # 10MB
    MAX_TITLE_LENGTH = 255
    MAX_SLUG_LENGTH = 255

    @staticmethod
    def validate_content(content: str) -> tuple[bool, str | None]:
        """Validate document content."""
        if not content:
            return False, "Content cannot be empty"
        if len(content) > DocumentContentValidator.MAX_CONTENT_LENGTH:
            return False, f"Content too long (max {DocumentContentValidator.MAX_CONTENT_LENGTH} characters)"
        return True, None

    @staticmethod
    def validate_title(title: str) -> tuple[bool, str | None]:
        """Validate document title."""
        if not title:
            return False, "Title cannot be empty"
        if len(title) > DocumentContentValidator.MAX_TITLE_LENGTH:
            return False, f"Title too long (max {DocumentContentValidator.MAX_TITLE_LENGTH} characters)"
        return True, None

    @staticmethod
    def validate_slug(slug: str) -> tuple[bool, str | None]:
        """Validate document slug."""
        if not slug:
            return False, "Slug cannot be empty"
        if len(slug) > DocumentContentValidator.MAX_SLUG_LENGTH:
            return False, f"Slug too long (max {DocumentContentValidator.MAX_SLUG_LENGTH} characters)"
        if not validate_slug(slug):
            return False, "Slug can only contain lowercase letters, numbers, hyphens, and underscores"
        return True, None

