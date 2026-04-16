from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest

from app.models import ToolDefinition
from app.services import capabilities_service, manifest_service


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


def test_build_runtime_manifest_contains_runtime_contract():
    manifest = manifest_service.build_runtime_manifest(_tool())

    assert manifest["name"] == "get_producthunt"
    assert manifest["base_url"] == "http://localhost:8000"
    assert manifest["runtime_endpoint"]["path"] == "/api/execute/get_producthunt"
    assert manifest["runtime_endpoint"]["url"] == "http://localhost:8000/api/execute/get_producthunt"
    assert manifest["runtime_response"]["payload_field"] == "data"
    assert manifest["runtime_response"]["raw_payload_field"] == "raw_result"
    assert manifest["billing"]["cost_per_call"] == 10
    assert manifest["auth"]["type"] == "bearer"
    assert manifest["auth"]["token_env_var"] == "FUSEKIT_TOKEN"
    assert manifest["auth"]["local_development_token"] == "demo-token-fusekit-2026"
    assert manifest["manifest_pointer"]["manifest_path"].endswith("get_producthunt.json")
    assert manifest["manifest_pointer"]["artifact_key"] == "manifests/get_producthunt.json"
    assert manifest["manifest_pointer"]["http_url"] == "http://localhost:8000/api/capabilities/get_producthunt/manifest"


@pytest.mark.asyncio
async def test_execute_capability_returns_tool_not_found(monkeypatch):
    async def fake_get_tool_definition(_tool_name: str):
        return None

    called = {"queued": False}

    async def fake_queue(_tool_name: str):
        called["queued"] = True

    monkeypatch.setattr(capabilities_service, "get_tool_definition", fake_get_tool_definition)
    monkeypatch.setattr(capabilities_service, "queue_missing_tool_integration", fake_queue)

    result = await capabilities_service.execute_capability(
        user_id=uuid.uuid4(),
        tool_name="missing_tool",
        arguments={},
    )

    assert result.is_error is True
    assert result.error_code == "TOOL_NOT_FOUND"
    assert called["queued"] is True
