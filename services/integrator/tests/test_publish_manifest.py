from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

import pytest

from app.models import IntegrationJob
from app.publishers import db_writer
from app.schemas import APISpecification, DiscoveryResult, GeneratedTool, TestResult


@pytest.mark.asyncio
async def test_publish_tool_writes_manifest_and_runtime(tmp_path, session_factory, monkeypatch):
    monkeypatch.setattr(db_writer, "DYNAMIC_TOOLS_DIR", tmp_path)
    monkeypatch.setattr(db_writer, "MANIFESTS_DIR", tmp_path / "manifests")

    job_id = uuid.uuid4()
    async with session_factory() as session:
        job = IntegrationJob(
            id=job_id,
            docs_url="https://docs.example.com",
            requested_tool_name="send_slack_message",
            status="running",
            current_stage="publish",
            attempts=1,
            triggered_by="user",
            created_at=datetime.now(timezone.utc),
        )
        session.add(job)
        await session.commit()
        await session.refresh(job)

        generated = GeneratedTool(
            name="send_slack_message",
            description="Send Slack messages",
            provider="Slack",
            input_schema={"type": "object", "properties": {"channel": {"type": "string"}}},
            output_schema={"type": "object", "properties": {"ok": {"type": "boolean"}}},
            implementation_module="app.tools.send_slack_message.execute",
            python_code="async def execute(**kwargs) -> str:\n    return 'ok'\n",
        )
        test_result = TestResult(success=True, final_code=generated.python_code, attempts=1)
        discovery = DiscoveryResult(
            provider_name="Slack",
            base_url="https://slack.com/api",
            auth_method="bearer",
            key_endpoints=["POST /chat.postMessage"],
        )
        api_spec = APISpecification(
            provider_name="Slack",
            base_url="https://slack.com/api",
            auth={"type": "bearer"},
            endpoints=[{"path": "/chat.postMessage", "method": "POST"}],
        )

        tool = await db_writer.publish_tool(
            session,
            job,
            generated,
            test_result,
            discovery=discovery,
            api_spec=api_spec,
        )

    assert tool is not None
    runtime_path = tmp_path / "send_slack_message.py"
    manifest_path = tmp_path / "manifests" / "send_slack_message.json"
    assert runtime_path.exists()
    assert manifest_path.exists()

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["tool_name"] == "send_slack_message"
    assert manifest["name"] == "send_slack_message"
    assert manifest["base_url"] == "http://localhost:8000"
    assert manifest["docs_url"] == "https://docs.example.com"
    assert manifest["api_spec"]["base_url"] == "https://slack.com/api"
    assert manifest["runtime_endpoint"]["url"] == "http://localhost:8000/api/execute/send_slack_message"
    assert manifest["manifest_endpoint"]["url"] == "http://localhost:8000/api/capabilities/send_slack_message/manifest"
    assert manifest["auth"]["token_env_var"] == "FUSEKIT_TOKEN"
    assert manifest["manifest_pointer"]["artifact_key"] == "manifests/send_slack_message.json"
