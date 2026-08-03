import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.main import app
from app.core.database import Base, get_db
from app.core.websocket_manager import ConnectionManager


TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

TestingSessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False,
)


@pytest.fixture
def manager():
    return ConnectionManager()


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
async def db_session():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestingSessionLocal() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def override_db(db_session: AsyncSession):
    async def _override():
        yield db_session

    app.dependency_overrides[get_db] = _override

    yield

    app.dependency_overrides.clear()