from __future__ import annotations

import asyncio
import uuid
from collections.abc import AsyncGenerator, Generator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.main import app
from app.models import Base, IntegrationJob


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture()
async def test_engine():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    try:
        yield engine
    finally:
        await engine.dispose()


@pytest.fixture()
async def session_factory(test_engine):
    return async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture()
async def db_session(session_factory) -> AsyncGenerator[AsyncSession, None]:
    async with session_factory() as session:
        yield session


@pytest.fixture()
async def seeded_job(session_factory) -> IntegrationJob:
    job_id = uuid.uuid4()
    async with session_factory() as session:
        job = IntegrationJob(
            id=job_id,
            docs_url="https://example.com/docs",
            requested_tool_name="example_tool",
            status="queued",
            current_stage="queued",
            triggered_by="user",
            attempts=0,
        )
        session.add(job)
        await session.commit()
        await session.refresh(job)
        return job


@pytest.fixture()
async def api_client(session_factory):
    from app.db import get_session
    from app.main import app

    async def _override_get_session():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = _override_get_session
    app.state.startup_errors = []
    app.state.tasks = set()

    try:
        transport = ASGITransport(app=app, lifespan="off")
    except TypeError:  # pragma: no cover
        transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()
