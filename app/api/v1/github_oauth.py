"""GitHub OAuth API endpoints."""

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import RedirectResponse
from app.api.v1.auth import get_current_user
from app.domain.models.user import User
from app.core.config import settings
import httpx

router = APIRouter()


@router.get("/authorize")
async def github_authorize(
    current_user: Annotated[User, Depends(get_current_user)] = None,
):
    """Redirect to GitHub OAuth authorization."""
    if not settings.github_client_id:
        raise HTTPException(
            status_code=500, detail="GitHub OAuth not configured"
        )

    # TODO: Store state in session/redis for CSRF protection
    state = "temp_state"  # Should be random and stored

    auth_url = (
        f"https://github.com/login/oauth/authorize"
        f"?client_id={settings.github_client_id}"
        f"&redirect_uri={settings.cors_origins_list[0]}/api/v1/github/callback"
        f"&scope=repo"
        f"&state={state}"
    )

    return RedirectResponse(url=auth_url)


@router.get("/callback")
async def github_callback(
    code: str = Query(...),
    state: str = Query(None),
    current_user: Annotated[User, Depends(get_current_user)] = None,
):
    """Handle GitHub OAuth callback."""
    if not settings.github_client_id or not settings.github_client_secret:
        raise HTTPException(
            status_code=500, detail="GitHub OAuth not configured"
        )

    # Exchange code for access token
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://github.com/login/oauth/access_token",
            data={
                "client_id": settings.github_client_id,
                "client_secret": settings.github_client_secret,
                "code": code,
            },
            headers={"Accept": "application/json"},
        )
        response.raise_for_status()
        token_data = response.json()

    access_token = token_data.get("access_token")
    if not access_token:
        raise HTTPException(
            status_code=400, detail="Failed to obtain access token"
        )

    # TODO: Store access_token in database associated with user
    # For now, just return it (in production, store securely)

    return {
        "status": "success",
        "message": "GitHub OAuth successful",
        # "access_token": access_token,  # Don't return in production
    }

