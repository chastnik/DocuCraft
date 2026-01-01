"""Comments API endpoints."""

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Path, Body
from app.domain.models.user import User
from app.api.v1.auth import get_current_user
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()


class CommentCreate(BaseModel):
    text: str
    parent_id: str | None = None


class CommentUpdate(BaseModel):
    text: str


class Comment(BaseModel):
    id: str
    document_id: str
    author_id: str | None
    author: str | None
    text: str
    parent_id: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


@router.get("/documents/{document_id}/comments", response_model=list[Comment])
async def get_document_comments(
    document_id: str = Path(...),
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    """Get comments for a document."""
    # TODO: Implement comment repository and service
    # For now, return empty list
    return []


@router.post("/documents/{document_id}/comments", response_model=Comment, status_code=status.HTTP_201_CREATED)
async def create_comment(
    document_id: str = Path(...),
    comment_data: CommentCreate = Body(...),
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    """Create a comment."""
    # TODO: Implement comment creation
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Comments not yet implemented")


@router.put("/comments/{comment_id}", response_model=Comment)
async def update_comment(
    comment_id: str = Path(...),
    comment_data: CommentUpdate = Body(...),
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    """Update a comment."""
    # TODO: Implement comment update
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Comments not yet implemented")


@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    comment_id: str = Path(...),
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    """Delete a comment."""
    # TODO: Implement comment deletion
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Comments not yet implemented")

