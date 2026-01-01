"""GitHub webhook utilities."""

import hmac
import hashlib
from typing import Any
from app.core.config import settings


def verify_webhook_signature(payload_body: bytes, signature_header: str, secret: str) -> bool:
    """Verify GitHub webhook signature."""
    if not signature_header:
        return False

    hash_object = hmac.new(secret.encode("utf-8"), msg=payload_body, digestmod=hashlib.sha256)
    expected_signature = "sha256=" + hash_object.hexdigest()

    return hmac.compare_digest(expected_signature, signature_header)


def parse_webhook_event(event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Parse webhook event payload."""
    result = {
        "event_type": event_type,
        "commit_hash": None,
        "branch": None,
        "files_changed": [],
    }

    if event_type == "push":
        result["commit_hash"] = payload.get("after")
        result["branch"] = payload.get("ref", "").replace("refs/heads/", "")
        commits = payload.get("commits", [])
        if commits:
            # Get files from all commits
            for commit in commits:
                result["files_changed"].extend(
                    commit.get("added", [])
                    + commit.get("modified", [])
                    + commit.get("removed", [])
                )
            # Remove duplicates
            result["files_changed"] = list(set(result["files_changed"]))

    elif event_type == "pull_request":
        pr = payload.get("pull_request", {})
        result["commit_hash"] = pr.get("head", {}).get("sha")
        result["branch"] = pr.get("head", {}).get("ref")
        # For PRs, we'd need to fetch the diff separately

    return result

