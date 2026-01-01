"""Authentication service."""

from app.domain.repositories.user_repository import UserRepository
from app.domain.models.user import UserCreate, UserLogin, User
from app.core.security import verify_password, get_password_hash, create_access_token
from app.core.exceptions import UnauthorizedError, ConflictError
from datetime import timedelta
from app.core.config import settings


class AuthService:
    """Authentication service."""

    def __init__(self, user_repository: UserRepository):
        """Initialize auth service."""
        self.user_repository = user_repository

    async def register(self, user_data: UserCreate) -> User:
        """Register a new user."""
        # Check if user with email exists
        existing_user = await self.user_repository.get_by_email(user_data.email)
        if existing_user:
            raise ConflictError("User with this email already exists")

        # Check if user with username exists
        existing_user = await self.user_repository.get_by_username(user_data.username)
        if existing_user:
            raise ConflictError("User with this username already exists")

        # Hash password
        hashed_password = get_password_hash(user_data.password)

        # Create user
        user = await self.user_repository.create(user_data, hashed_password)
        return User.model_validate(user)

    async def login(self, login_data: UserLogin) -> tuple[User, str]:
        """Login user and return user with access token."""
        # Get user by email
        user = await self.user_repository.get_by_email(login_data.email)
        if not user:
            raise UnauthorizedError("Invalid email or password")

        # Verify password
        if not verify_password(login_data.password, user.hashed_password):
            raise UnauthorizedError("Invalid email or password")

        # Check if user is active
        if not user.is_active:
            raise UnauthorizedError("User account is disabled")

        # Create access token
        access_token = create_access_token(
            data={"sub": user.id},
            expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
        )

        return User.model_validate(user), access_token

    async def get_current_user(self, user_id: str) -> User:
        """Get current user by ID."""
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise UnauthorizedError("User not found")
        return User.model_validate(user)

