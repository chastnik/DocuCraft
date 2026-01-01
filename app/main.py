"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.core.config import settings
from app.core.middleware import LoggingMiddleware, ErrorHandlingMiddleware
import logging
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO if settings.debug else logging.WARNING,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
from app.api.v1 import auth, projects, documents, git, github_oauth, ai, openapi, admin
from app.api import websocket

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="DocuCraft - автоматическая генерация и сопровождение документации",
    debug=settings.debug,
)

# Middleware
app.add_middleware(ErrorHandlingMiddleware)
app.add_middleware(LoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(projects.router, prefix="/api/v1/projects", tags=["projects"])
app.include_router(documents.router, prefix="/api/v1/documents", tags=["documents"])
app.include_router(git.router, prefix="/api/v1/git", tags=["git"])
app.include_router(github_oauth.router, prefix="/api/v1/github", tags=["github"])
app.include_router(ai.router, prefix="/api/v1/ai", tags=["ai"])
app.include_router(openapi.router, prefix="/api/v1/openapi", tags=["openapi"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["admin"])

# WebSocket endpoint
from fastapi import WebSocket as FastAPIWebSocket, Query

@app.websocket("/ws/documents/{document_id}")
async def websocket_route(
    websocket: FastAPIWebSocket,
    document_id: str,
    token: str = Query(None),
):
    """WebSocket route for document editing."""
    from app.api.websocket import websocket_endpoint
    from app.api.deps import get_db
    
    async for db in get_db():
        await websocket_endpoint(websocket, document_id, token, db)
        break


# Mount static files
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/")
async def root():
    """Root endpoint - serve login page."""
    static_file = os.path.join(static_dir, "index.html")
    if os.path.exists(static_file):
        return FileResponse(static_file)
    return {
        "message": "DocuCraft API",
        "version": "0.1.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}

