from typing import AsyncIterator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app


@pytest_asyncio.fixture
async def async_session_maker() -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    """In-memory SQLite DB (single shared connection) with all tables created,
    wired up as the app's `get_db` dependency for the duration of the test."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async def _get_db_override():
        async with maker() as session:
            yield session

    app.dependency_overrides[get_db] = _get_db_override
    try:
        yield maker
    finally:
        app.dependency_overrides.pop(get_db, None)
        await engine.dispose()


@pytest_asyncio.fixture
async def client(async_session_maker) -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
