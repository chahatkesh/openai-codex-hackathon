from __future__ import annotations

import uuid

import pytest

from app import mcp_server
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

    monkeypatch.setattr(mcp_server, "async_session", fake_async_session_factory)
    monkeypatch.setattr(mcp_server, "forward_job_non_blocking", fake_forward)

    await mcp_server._queue_missing_tool_integration("send_slack_message")

    assert len(fake_session.added) == 1
    job = fake_session.added[0]
    assert job.triggered_by == "mcp_tool_miss"
    assert job.docs_url == "mcp://tool-miss/send_slack_message"
    assert captured["requested_tool_name"] == "send_slack_message"


@pytest.mark.asyncio
async def test_call_tool_missing_returns_tool_not_found(monkeypatch):
    async def fake_demo_user_id():
        return uuid.uuid4()

    # first DB session lookup for tool returns none
    fake_lookup_session = FakeSession(execute_results=[DummyResult(None)])

    def fake_async_session_factory():
        return _SessionCM(fake_lookup_session)

    called = {"queued": False}

    async def fake_queue(_name):
        called["queued"] = True

    monkeypatch.setattr(mcp_server, "_get_demo_user_id", fake_demo_user_id)
    monkeypatch.setattr(mcp_server, "async_session", fake_async_session_factory)
    monkeypatch.setattr(mcp_server, "_queue_missing_tool_integration", fake_queue)

    payload = await mcp_server.call_tool("send_slack_message", {})

    assert called["queued"] is True
    assert "TOOL_NOT_FOUND" in payload[0].text
