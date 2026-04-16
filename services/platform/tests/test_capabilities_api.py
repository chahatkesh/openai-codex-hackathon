from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest

from app.api.capabilities import get_capability_manifest_http
from app.models import ToolDefinition


def _tool(name: str = "get_producthunt") -> ToolDefinition:
    now = datetime.now(timezone.utc)
    return ToolDefinition(
        id=uuid.uuid4(),
        name=name,
        description="desc",
        provider="demo",
        cost_per_call=10,
        status="live",
        input_schema={
            "type": "object",
            "required": ["category"],
            "properties": {"category": {"type": "string"}},
        },
        output_schema={"type": "object", "properties": {"result": {"type": "string"}}},
        category="data_retrieval",
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
