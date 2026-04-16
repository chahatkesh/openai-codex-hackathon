from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

import pytest

from app.models import ToolDefinition
from app.tools import get_capability_manifest


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
async def test_get_capability_manifest_returns_json_manifest(monkeypatch):
    async def fake_get_tool_definition(_name: str):
        return _tool()

    monkeypatch.setattr(get_capability_manifest, "get_tool_definition", fake_get_tool_definition)

    payload = await get_capability_manifest.execute("get_producthunt")
    manifest = json.loads(payload)

    assert manifest["name"] == "get_producthunt"
    assert manifest["base_url"] == "http://localhost:8000"
    assert manifest["runtime_endpoint"]["path"] == "/api/execute/get_producthunt"
    assert manifest["manifest_endpoint"]["url"] == "http://localhost:8000/api/capabilities/get_producthunt/manifest"
    assert manifest["auth"]["token_env_var"] == "FUSEKIT_TOKEN"
    assert manifest["manifest_pointer"]["manifest_path"].endswith("get_producthunt.json")
