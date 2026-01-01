"""Authentication API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import Annotated
from app.domain.models.user import User, UserCreate, Token
from app.domain.services.auth_service import AuthService
from app.api.deps import get_user_repository, get_db
from app.domain.repositories.user_repository import UserRepository
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_auth_service(
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
) -> AuthService:
    """Get auth service."""
    return AuthService(user_repo)


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> User:
    """Get current authenticated user."""
    from app.core.security import decode_access_token
    from app.core.exceptions import UnauthorizedError

    payload = decode_access_token(token)
    if payload is None:
        raise UnauthorizedError("Invalid token")

    user_id: str | None = payload.get("sub")
    if user_id is None:
        raise UnauthorizedError("Invalid token payload")

    return await auth_service.get_current_user(user_id)


@router.get("/setup-status")
async def get_setup_status(
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
):
    """Check if system needs initial admin setup."""
    user_count = await user_repo.count()
    return {
        "needs_setup": user_count == 0,
        "user_count": user_count,
    }


@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
):
    """Register a new user. First user automatically becomes superuser."""
    # Check if this is the first user
    user_count = await user_repo.count()
    is_first_user = user_count == 0
    
    return await auth_service.register(user_data, is_superuser=is_first_user)


@router.post("/login", response_model=Token)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
):
    """Login user and get access token."""
    from app.domain.models.user import UserLogin

    login_data = UserLogin(email=form_data.username, password=form_data.password)
    user, access_token = await auth_service.login(login_data)
    return Token(access_token=access_token, token_type="bearer")


@router.get("/me", response_model=User)
async def get_me(
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Get current user information."""
    return current_user

