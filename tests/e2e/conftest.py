from __future__ import annotations

import asyncio
import os
from collections.abc import AsyncIterator
from dataclasses import dataclass

import pytest

httpx = pytest.importorskip("httpx")


@dataclass
class ServiceConfig:
    api_base_url: str
    mcp_sse_url: str


@pytest.fixture(scope="session")
def service_config() -> ServiceConfig:
    api_base_url = os.getenv("API_BASE_URL", "http://localhost:8000")
    mcp_sse_url = os.getenv("MCP_SSE_URL", f"{api_base_url}/mcp/sse")
    return ServiceConfig(api_base_url=api_base_url, mcp_sse_url=mcp_sse_url)


@pytest.fixture(scope="session")
def event_loop() -> AsyncIterator[asyncio.AbstractEventLoop]:
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def api_client() -> AsyncIterator[httpx.AsyncClient]:
    async with httpx.AsyncClient(timeout=30) as client:
        yield client
