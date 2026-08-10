from __future__ import annotations

from collections import defaultdict
from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.connections: dict[int, set[WebSocket]] = defaultdict(set)

    async def connect(
        self,
        websocket: WebSocket,
        user_id: int,
    ) -> None:
        await websocket.accept()
        self.connections[user_id].add(websocket)

    def disconnect(
        self,
        websocket: WebSocket,
        user_id: int,
    ) -> None:
        if user_id not in self.connections:
            return

        self.connections[user_id].discard(websocket)

        if not self.connections[user_id]:
            del self.connections[user_id]

    def is_online(self, user_id: int) -> bool:
        return user_id in self.connections and bool(self.connections[user_id])

    async def send_to_user(
        self,
        user_id: int,
        payload: dict,
    ) -> None:
        for ws in self.connections.get(user_id, set()).copy():
            await ws.send_json(payload)

    async def broadcast(
        self,
        payload: dict,
        exclude_user: int | None = None,
    ) -> None:
        dead_connections = []

        for user_id, sockets in self.connections.items():
            if user_id == exclude_user:
                continue

            for ws in sockets.copy():
                try:
                    await ws.send_json(payload)
                except Exception:
                    dead_connections.append((user_id, ws))

        for user_id, ws in dead_connections:
            self.disconnect(ws, user_id)


manager = ConnectionManager()