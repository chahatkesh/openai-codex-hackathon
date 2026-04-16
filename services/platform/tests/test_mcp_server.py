from __future__ import annotations

import uuid

import pytest

from app import mcp_server
from app.services.capabilities_service import ExecutionResult
from app.services.integrations_service import build_tool_miss_docs_url
from tests.helpers import DummyResult, FakeSession


class _SessionCM:
    def __init__(self, session):
        self.session = session

    async def __aenter__(self):
        return self.session

    async def __aexit__(self, exc_type, exc, tb):
        return False


@pytest.mark.asyncio
async def test_queue_missing_tool_integration_persists_job(monkeypatch):
    fake_session = FakeSession()

    def fake_async_session_factory():
        return _SessionCM(fake_session)

    captured = {}

    def fake_forward(payload):
        captured["requested_tool_name"] = payload.requested_tool_name
        captured["docs_url"] = payload.docs_url

    monkeypatch.setattr("app.services.capabilities_service.async_session", fake_async_session_factory)
    monkeypatch.setattr("app.services.capabilities_service.forward_job_non_blocking", fake_forward)

    await mcp_server._queue_missing_tool_integration("send_slack_message")

    assert len(fake_session.added) == 1
    job = fake_session.added[0]
    assert job.triggered_by == "mcp_tool_miss"
    assert job.docs_url == build_tool_miss_docs_url("send_slack_message")
    assert captured["requested_tool_name"] == "send_slack_message"


@pytest.mark.asyncio
async def test_call_tool_missing_returns_tool_not_found(monkeypatch):
    async def fake_demo_user_id():
        return uuid.uuid4()

    async def fake_execute_capability(**_kwargs):
        return ExecutionResult(
            ok=False,
            tool_name="send_slack_message",
            text="TOOL_NOT_FOUND: 'send_slack_message' is not in the catalog. An integration job has been queued. Retry in a few minutes.",
            is_error=True,
            error_code="TOOL_NOT_FOUND",
        )

    monkeypatch.setattr(mcp_server, "_get_demo_user_id", fake_demo_user_id)
    monkeypatch.setattr(mcp_server, "execute_capability", fake_execute_capability)

    payload = await mcp_server.call_tool("send_slack_message", {})

    assert "TOOL_NOT_FOUND" in payload[0].text
