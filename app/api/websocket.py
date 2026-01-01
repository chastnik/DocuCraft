"""WebSocket endpoints for realtime collaboration."""

from typing import Dict, Set
from fastapi import WebSocket, WebSocketDisconnect, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db
from app.domain.repositories.document_repository import DocumentRepository
from app.infrastructure.database.repositories.document_repository_impl import DocumentRepositoryImpl
from app.core.security import decode_access_token
from app.core.exceptions import UnauthorizedError
import json
import asyncio


class ConnectionManager:
    """Manages WebSocket connections for realtime collaboration."""

    def __init__(self):
        """Initialize connection manager."""
        # document_id -> Set[WebSocket]
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # websocket -> user_id
        self.connection_users: Dict[WebSocket, str] = {}

    async def connect(self, websocket: WebSocket, document_id: str, user_id: str):
        """Connect a user to a document."""
        await websocket.accept()

        if document_id not in self.active_connections:
            self.active_connections[document_id] = set()

        self.active_connections[document_id].add(websocket)
        self.connection_users[websocket] = user_id

        # Notify other users
        await self.broadcast_to_document(
            document_id,
            {
                "type": "user_joined",
                "user_id": user_id,
                "message": f"User {user_id} joined the document",
            },
            exclude=websocket,
        )

    def disconnect(self, websocket: WebSocket, document_id: str):
        """Disconnect a user from a document."""
        if document_id in self.active_connections:
            self.active_connections[document_id].discard(websocket)
            if not self.active_connections[document_id]:
                del self.active_connections[document_id]

        user_id = self.connection_users.pop(websocket, None)

        # Notify other users
        if user_id:
            asyncio.create_task(
                self.broadcast_to_document(
                    document_id,
                    {
                        "type": "user_left",
                        "user_id": user_id,
                        "message": f"User {user_id} left the document",
                    },
                )
            )

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send a message to a specific connection."""
        try:
            await websocket.send_json(message)
        except Exception:
            pass  # Connection might be closed

    async def broadcast_to_document(
        self, document_id: str, message: dict, exclude: WebSocket | None = None
    ):
        """Broadcast a message to all connections for a document."""
        if document_id not in self.active_connections:
            return

        disconnected = set()
        for connection in self.active_connections[document_id]:
            if connection == exclude:
                continue
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.add(connection)

        # Clean up disconnected connections
        for conn in disconnected:
            self.disconnect(conn, document_id)

    def get_active_users(self, document_id: str) -> list[str]:
        """Get list of active user IDs for a document."""
        if document_id not in self.active_connections:
            return []

        users = []
        for websocket in self.active_connections[document_id]:
            user_id = self.connection_users.get(websocket)
            if user_id:
                users.append(user_id)

        return list(set(users))


manager = ConnectionManager()


async def get_user_from_token(token: str | None) -> str:
    """Get user ID from JWT token."""
    if not token:
        raise UnauthorizedError("Token required")

    payload = decode_access_token(token)
    if payload is None:
        raise UnauthorizedError("Invalid token")

    user_id: str | None = payload.get("sub")
    if user_id is None:
        raise UnauthorizedError("Invalid token payload")

    return user_id


async def websocket_endpoint(
    websocket: WebSocket,
    document_id: str,
    token: str | None = None,
    db: AsyncSession | None = None,
):
    """WebSocket endpoint for realtime document editing."""
    # Authenticate user
    try:
        user_id = await get_user_from_token(token)
    except Exception as e:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # Get database session if not provided
    if db is None:
        from app.api.deps import get_db
        async for session in get_db():
            db = session
            break

    # Verify document access
    document_repo: DocumentRepository = DocumentRepositoryImpl(db)
    document = await document_repo.get_by_id(document_id)
    if not document:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Document not found")
        return

    # Connect
    await manager.connect(websocket, document_id, user_id)

    try:
        # Send initial document state
        await manager.send_personal_message(
            {
                "type": "document_state",
                "content": document.content,
                "version": document.version,
            },
            websocket,
        )

        # Send active users list
        active_users = manager.get_active_users(document_id)
        await manager.send_personal_message(
            {
                "type": "active_users",
                "users": active_users,
            },
            websocket,
        )

        # Listen for messages
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                message_type = message.get("type")

                if message_type == "content_change":
                    # Broadcast content change to other users
                    await manager.broadcast_to_document(
                        document_id,
                        {
                            "type": "content_change",
                            "user_id": user_id,
                            "changes": message.get("changes"),
                            "version": message.get("version"),
                        },
                        exclude=websocket,
                    )

                elif message_type == "cursor_position":
                    # Broadcast cursor position
                    await manager.broadcast_to_document(
                        document_id,
                        {
                            "type": "cursor_position",
                            "user_id": user_id,
                            "position": message.get("position"),
                        },
                        exclude=websocket,
                    )

                elif message_type == "selection":
                    # Broadcast text selection
                    await manager.broadcast_to_document(
                        document_id,
                        {
                            "type": "selection",
                            "user_id": user_id,
                            "selection": message.get("selection"),
                        },
                        exclude=websocket,
                    )

                elif message_type == "ping":
                    # Respond to ping
                    await manager.send_personal_message(
                        {"type": "pong"},
                        websocket,
                    )

            except json.JSONDecodeError:
                await manager.send_personal_message(
                    {"type": "error", "message": "Invalid JSON"},
                    websocket,
                )

    except WebSocketDisconnect:
        manager.disconnect(websocket, document_id)

