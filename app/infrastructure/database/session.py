"""Database session management."""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from app.core.config import settings

# Async engine for SQLAlchemy 2.0
async_engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    future=True,
)

# Sync engine for Alembic
sync_engine = create_engine(
    settings.database_url_sync,
    echo=settings.debug,
)

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Sync session factory (for Alembic)
SessionLocal = sessionmaker(
    bind=sync_engine,
    autocommit=False,
    autoflush=False,
)


async def get_async_session() -> AsyncSession:
    """Get async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


def get_sync_session():
    """Get sync database session (for Alembic)."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

