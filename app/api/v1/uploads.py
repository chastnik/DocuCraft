"""File upload API endpoints."""

from typing import Annotated
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from fastapi.responses import FileResponse
from app.api.v1.auth import get_current_user
from app.domain.models.user import User
from app.core.config import settings
import os
import uuid
from pathlib import Path

# Try to use aiofiles, fallback to standard file operations
try:
    import aiofiles
    HAS_AIOFILES = True
except ImportError:
    HAS_AIOFILES = False

router = APIRouter()

# Create uploads directory if it doesn't exist
UPLOADS_DIR = Path(settings.storage_path) / "uploads" / "images"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


@router.post("/images")
async def upload_image(
    file: UploadFile = File(...),
    current_user: Annotated[User, Depends(get_current_user)] = None,
):
    """Upload an image file."""
    # Check file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Generate unique filename
    file_id = str(uuid.uuid4())
    filename = f"{file_id}{file_ext}"
    file_path = UPLOADS_DIR / filename

    # Read file content
    content = await file.read()
    
    # Check file size
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE / 1024 / 1024}MB"
        )

    # Save file
    if HAS_AIOFILES:
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(content)
    else:
        # Fallback to synchronous file write
        with open(file_path, "wb") as f:
            f.write(content)

    # Return URL
    return {
        "url": f"/api/v1/uploads/images/{filename}",
        "filename": filename,
        "size": len(content),
    }


@router.get("/images/{filename}")
async def get_image(filename: str):
    """Get uploaded image."""
    file_path = UPLOADS_DIR / filename
    
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")
    
    # Security check: ensure file is in uploads directory
    try:
        file_path.resolve().relative_to(UPLOADS_DIR.resolve())
    except ValueError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    
    return FileResponse(file_path)

