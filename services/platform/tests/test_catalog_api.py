from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest

from app.api.catalog import catalog_stats, list_catalog, recent_catalog
from app.models import ToolDefinition
from tests.helpers import DummyResult, FakeSession



def _tool(name: str, created_at: datetime, status: str = "live", category: str = "other") -> ToolDefinition:
    return ToolDefinition(
        id=uuid.uuid4(),
        name=name,
        description=f"desc for {name}",
        provider="demo",
        cost_per_call=10,
        status=status,
        input_schema={"type": "object"},
        output_schema={"type": "object"},
        category=category,
        source="seed",
        version=1,
        implementation_module=f"tools.{name}",
        created_at=created_at,
        updated_at=created_at,
    )


@pytest.mark.asyncio
async def test_list_catalog_returns_serialized_items():
    now = datetime.now(timezone.utc)
    tools = [_tool("scrape_url", now), _tool("send_sms", now)]
    session = FakeSession(execute_results=[DummyResult(tools)])

    payload = await list_catalog(session=session)

    assert len(payload) == 2
    assert payload[0]["name"] == "scrape_url"


@pytest.mark.asyncio
async def test_recent_catalog_returns_recent_items():
    now = datetime.now(timezone.utc)
    recent = _tool("recent_tool", now - timedelta(hours=2))
    session = FakeSession(execute_results=[DummyResult([recent])])

    payload = await recent_catalog(session=session)

    assert len(payload) == 1
    assert payload[0]["name"] == "recent_tool"


@pytest.mark.asyncio
async def test_catalog_stats_computes_counts():
    now = datetime.now(timezone.utc)
    tools = [
        _tool("a", now, status="live", category="search"),
        _tool("b", now, status="pending_credentials", category="search"),
    ]
    session = FakeSession(execute_results=[DummyResult(tools)])

    payload = await catalog_stats(session=session)

    assert payload["total"] == 2
    assert payload["live"] == 1
    assert payload["pending_credentials"] == 1
    assert payload["by_category"]["search"] == 2
