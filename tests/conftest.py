import pytest

from app.core.websocket_manager import ConnectionManager


@pytest.fixture
def manager():
    return ConnectionManager()