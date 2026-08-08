from __future__ import annotations

import logging

from fastapi import APIRouter, Cookie, Depends, WebSocket, WebSocketDisconnect, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.constants import ACCESS_TOKEN_COOKIE
from app.core.database import get_db
from app.core.security import decode_access_token
from app.core.websocket_manager import manager
from app.models.user import User

logger = logging.getLogger("ws")
router = APIRouter()


def _origin_allowed(websocket: WebSocket) -> bool:
    origin = websocket.headers.get("origin")
    if not origin:
        return True
    return origin in get_settings().cors_origins


async def _authenticate(
    db: AsyncSession,
    access_token: str | None,
) -> User | None:
    if access_token is None:
        return None
    email = decode_access_token(access_token)
    if email is None:
        return None
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


@router.websocket("/ws/sightings")
async def sightings_socket(
    websocket: WebSocket,
    access_token: str | None = Cookie(default=None, alias=ACCESS_TOKEN_COOKIE),
    db: AsyncSession = Depends(get_db),
) -> None:
    if not _origin_allowed(websocket):
        logger.warning("ws rejected: disallowed origin=%s", websocket.headers.get("origin"))
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    user = await _authenticate(db, access_token)
    if user is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await manager.connect(websocket, user.id)
    try:
        while True:
            # Clients don't need to send anything; incoming frames are just a
            # liveness signal / ping-pong.
            await websocket.receive_text()
    except WebSocketDisconnect:
        logger.info("User %s disconnected", user.id)
    except Exception:
        logger.exception("Unexpected websocket error for user %s", user.id)
    finally:
        manager.disconnect(websocket, user.id)