from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest

from app.api.capabilities import (
    capability_stats,
    get_capability_detail,
    get_capability_manifest_http,
    list_capabilities,
    recent_capabilities,
)
from app.models import ToolDefinition
from tests.helpers import DummyResult, FakeSession


def _tool(
    name: str = "get_producthunt",
    *,
    status: str = "live",
    category: str = "data_retrieval",
) -> ToolDefinition:
    now = datetime.now(timezone.utc)
    return ToolDefinition(
        id=uuid.uuid4(),
        name=name,
        description="desc",
        provider="demo",
        cost_per_call=10,
        status=status,
        input_schema={
            "type": "object",
            "required": ["category"],
            "properties": {"category": {"type": "string"}},
        },
        output_schema={"type": "object", "properties": {"result": {"type": "string"}}},
        category=category,
        source="seed",
        version=1,
        implementation_module=f"app.tools.{name}",
        created_at=now,
        updated_at=now,
    )


@pytest.mark.asyncio
async def test_get_capability_manifest_http_returns_runtime_contract(monkeypatch):
    async def fake_get_tool_definition(_name: str):
        return _tool()

    monkeypatch.setattr("app.api.capabilities.get_tool_definition", fake_get_tool_definition)

    payload = await get_capability_manifest_http("get_producthunt")

    assert payload["name"] == "get_producthunt"
    assert payload["runtime_endpoint"]["path"] == "/api/execute/get_producthunt"
    assert payload["manifest_pointer"]["manifest_path"].endswith("get_producthunt.json")
    assert payload["manifest_endpoint"]["url"] == "http://localhost:8000/api/capabilities/get_producthunt/manifest"


@pytest.mark.asyncio
async def test_list_capabilities_returns_runtime_metadata():
    session = FakeSession(execute_results=[DummyResult([_tool("get_producthunt"), _tool("send_sms")])])

    payload = await list_capabilities(session=session)

    assert len(payload) == 2
    assert payload[0]["runtime_endpoint"]["url"].startswith("http://localhost:8000/api/execute/")
    assert payload[0]["manifest_endpoint"]["url"].startswith("http://localhost:8000/api/capabilities/")
    assert payload[0]["detail_endpoint"]["url"].startswith("http://localhost:8000/api/capabilities/")
    assert payload[0]["artifacts"]["preferred_source"] in {"local", "s3"}


@pytest.mark.asyncio
async def test_get_capability_detail_returns_manifest(monkeypatch):
    async def fake_get_tool_definition(_name: str):
        return _tool()

    monkeypatch.setattr("app.api.capabilities.get_tool_definition", fake_get_tool_definition)

    payload = await get_capability_detail("get_producthunt")

    assert payload["name"] == "get_producthunt"
    assert payload["manifest"]["runtime_endpoint"]["url"] == "http://localhost:8000/api/execute/get_producthunt"
    assert payload["manifest"]["artifacts"]["manifest"]["artifact_key"] == "manifests/get_producthunt.json"


@pytest.mark.asyncio
async def test_recent_capabilities_returns_runtime_metadata():
    session = FakeSession(execute_results=[DummyResult([_tool("recent_capability")])])

    payload = await recent_capabilities(session=session)

    assert len(payload) == 1
    assert payload[0]["name"] == "recent_capability"
    assert payload[0]["runtime_endpoint"]["path"] == "/api/execute/recent_capability"


@pytest.mark.asyncio
async def test_capability_stats_computes_counts():
    session = FakeSession(
        execute_results=[
            DummyResult(
                [
                    _tool("a", status="live"),
                    _tool("b", status="pending_credentials"),
                ]
            )
        ]
    )

    payload = await capability_stats(session=session)

    assert payload["total"] == 2
    assert payload["live"] == 1
    assert payload["pending_credentials"] == 1
