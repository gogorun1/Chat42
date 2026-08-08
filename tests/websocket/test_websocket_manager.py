"""
Run: pytest tests/websocket/test_websocket_manager.py -v

These test the ConnectionManager in isolation with a fake WebSocket, so no
FastAPI app, DB, or real socket is needed — the fastest tier of the pyramid.
"""
from __future__ import annotations

import pytest

from app.core.websocket_manager import ConnectionManager


class FakeWebSocket:

    def __init__(self, fail_on_send: bool = False):
        self.accepted = False
        self.sent: list[dict] = []
        self.fail_on_send = fail_on_send

    async def accept(self):
        self.accepted = True

    async def send_json(self, payload: dict):
        if self.fail_on_send:
            raise ConnectionResetError("simulated dropped connection")
        self.sent.append(payload)


@pytest.mark.asyncio
async def test_connect_accepts_and_tracks_user(manager: ConnectionManager):
    user_id = 1
    ws = FakeWebSocket()

    await manager.connect(ws, user_id)

    assert ws.accepted
    assert manager.is_online(user_id)


@pytest.mark.asyncio
async def test_disconnect_removes_user_when_last_socket_closes(manager: ConnectionManager):
    user_id = 1
    ws = FakeWebSocket()
    await manager.connect(ws, user_id)

    manager.disconnect(ws, user_id)

    assert not manager.is_online(user_id)


@pytest.mark.asyncio
async def test_user_with_two_tabs_stays_online_until_both_disconnect(manager: ConnectionManager):
    user_id = 1
    ws1, ws2 = FakeWebSocket(), FakeWebSocket()
    await manager.connect(ws1, user_id)
    await manager.connect(ws2, user_id)

    manager.disconnect(ws1, user_id)
    assert manager.is_online(user_id)  # ws2 still connected

    manager.disconnect(ws2, user_id)
    assert not manager.is_online(user_id)


@pytest.mark.asyncio
async def test_send_to_user_only_reaches_that_user(manager: ConnectionManager):
    alice, bob = 1, 2
    alice_ws, bob_ws = FakeWebSocket(), FakeWebSocket()
    await manager.connect(alice_ws, alice)
    await manager.connect(bob_ws, bob)

    await manager.send_to_user(alice, {"hello": "alice"})

    assert len(alice_ws.sent) == 1
    assert len(bob_ws.sent) == 0


@pytest.mark.asyncio
async def test_broadcast_reaches_everyone_except_excluded_user(manager: ConnectionManager):
    alice, bob = 1, 2
    alice_ws, bob_ws = FakeWebSocket(), FakeWebSocket()
    await manager.connect(alice_ws, alice)
    await manager.connect(bob_ws, bob)

    await manager.broadcast({"message": "cat spotted"}, exclude_user=alice)

    assert len(alice_ws.sent) == 0  # the reporter doesn't get their own broadcast
    assert len(bob_ws.sent) == 1


@pytest.mark.asyncio
async def test_broadcast_survives_a_dead_socket(manager: ConnectionManager):
    alive_user, dead_user = 1, 2
    alive_ws = FakeWebSocket()
    dead_ws = FakeWebSocket(fail_on_send=True)
    await manager.connect(alive_ws, alive_user)
    await manager.connect(dead_ws, dead_user)

    await manager.broadcast({"message": "cat spotted"})

    assert len(alive_ws.sent) == 1
    assert not manager.is_online(dead_user)  # dead socket got cleaned up

@pytest.mark.asyncio
async def test_send_to_offline_user_does_not_fail(manager: ConnectionManager):
    await manager.send_to_user(
        999,
        {"message": "hello"}
    )

    assert not manager.is_online(999)

def test_disconnect_unknown_user_is_safe(manager: ConnectionManager):
    ws = FakeWebSocket()

    manager.disconnect(ws, 999)

    assert not manager.is_online(999)

@pytest.mark.asyncio
async def test_send_to_user_reaches_all_user_connections(
    manager: ConnectionManager
):
    user_id = 1

    ws1 = FakeWebSocket()
    ws2 = FakeWebSocket()

    await manager.connect(ws1, user_id)
    await manager.connect(ws2, user_id)

    await manager.send_to_user(
        user_id,
        {"hello": "world"}
    )

    assert len(ws1.sent) == 1
    assert len(ws2.sent) == 1

@pytest.mark.asyncio
async def test_broadcast_reaches_all_connections(manager):

    alice1 = FakeWebSocket()
    alice2 = FakeWebSocket()
    bob1 = FakeWebSocket()

    await manager.connect(alice1, 1)
    await manager.connect(alice2, 1)
    await manager.connect(bob1, 2)

    await manager.broadcast(
        {"message": "cat spotted"}
    )

    assert len(alice1.sent) == 1
    assert len(alice2.sent) == 1
    assert len(bob1.sent) == 1

@pytest.mark.asyncio
async def test_dead_socket_does_not_remove_alive_connection(
    manager: ConnectionManager
):
    user_id = 1

    alive = FakeWebSocket()
    dead = FakeWebSocket(fail_on_send=True)

    await manager.connect(alive, user_id)
    await manager.connect(dead, user_id)

    await manager.broadcast({"msg": "test"})

    assert len(alive.sent) == 1
    assert manager.is_online(user_id)

@pytest.mark.asyncio
async def test_same_socket_connected_twice_only_stored_once(
    manager: ConnectionManager
):
    ws = FakeWebSocket()

    await manager.connect(ws, 1)
    await manager.connect(ws, 1)

    assert len(manager.connections[1]) == 1