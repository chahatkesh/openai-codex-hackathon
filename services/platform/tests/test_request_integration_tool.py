from __future__ import annotations

import json
import uuid

import pytest

from app.tools import request_integration
from app.models import ToolDefinition
from tests.helpers import DummyResult, FakeSession


class _SessionCM:
    def __init__(self, session):
        self.session = session

    async def __aenter__(self):
        return self.session

    async def __aexit__(self, exc_type, exc, tb):
        return False


@pytest.mark.asyncio
async def test_request_integration_creates_job_and_forwards(monkeypatch):
    fake_session = FakeSession()

    def fake_async_session_factory():
        return _SessionCM(fake_session)

    created_job_id = uuid.uuid4()

    async def fake_create(session, **kwargs):
        assert session is fake_session
        job = type("Job", (), {})()
        job.id = created_job_id
        job.docs_url = kwargs["docs_url"]
        job.requested_tool_name = kwargs["requested_tool_name"]
        job.triggered_by = kwargs["requested_by"]
        return job

    captured = {}

    def fake_forward(payload):
        captured["job_id"] = payload.job_id
        captured["docs_url"] = payload.docs_url
        captured["requested_tool_name"] = payload.requested_tool_name

    monkeypatch.setattr(request_integration, "async_session", fake_async_session_factory)
    monkeypatch.setattr(request_integration, "create_integration_job", fake_create)
    monkeypatch.setattr(request_integration, "forward_job_non_blocking", fake_forward)

    response = await request_integration.execute(
        capability_description="Send Slack messages to a channel",
        requested_tool_name="send_slack_message",
    )
    payload = json.loads(response)

    assert payload["status"] == "integration_requested"
    assert payload["job_id"] == str(created_job_id)
    assert captured["job_id"] == str(created_job_id)
    assert captured["requested_tool_name"] == "send_slack_message"
    assert "send%20slack%20message+API+documentation" in captured["docs_url"]


@pytest.mark.asyncio
async def test_request_integration_prefers_explicit_docs_url(monkeypatch):
    fake_session = FakeSession()

    def fake_async_session_factory():
        return _SessionCM(fake_session)

    async def fake_create(session, **kwargs):
        job = type("Job", (), {})()
        job.id = uuid.uuid4()
        job.docs_url = kwargs["docs_url"]
        job.requested_tool_name = kwargs["requested_tool_name"]
        job.triggered_by = kwargs["requested_by"]
        return job

    captured = {}

    def fake_forward(payload):
        captured["docs_url"] = payload.docs_url

    monkeypatch.setattr(request_integration, "async_session", fake_async_session_factory)
    monkeypatch.setattr(request_integration, "create_integration_job", fake_create)
    monkeypatch.setattr(request_integration, "forward_job_non_blocking", fake_forward)

    await request_integration.execute(
        capability_description="Send email via Resend",
        docs_url="https://resend.com/docs/api-reference/emails",
        requested_tool_name="send_email_via_resend",
    )

    assert captured["docs_url"] == "https://resend.com/docs/api-reference/emails"


@pytest.mark.asyncio
async def test_request_integration_returns_manifest_when_tool_exists(monkeypatch):
    existing_tool = ToolDefinition(
        id=uuid.uuid4(),
        name="send_email",
        description="Send email",
        provider="resend",
        cost_per_call=10,
        status="live",
        input_schema={"type": "object"},
        output_schema={"type": "object"},
        category="communication",
        source="seed",
        version=1,
        implementation_module="app.tools.send_email",
    )

    fake_session = FakeSession(execute_results=[DummyResult(existing_tool)])

    def fake_async_session_factory():
        return _SessionCM(fake_session)

    monkeypatch.setattr(request_integration, "async_session", fake_async_session_factory)

    response = await request_integration.execute(
        capability_description="Send email",
        requested_tool_name="send_email",
    )
    payload = json.loads(response)

    assert payload["status"] == "already_available"
    assert payload["manifest"]["tool_name"] == "send_email"
    assert payload["pointer"]["manifest_path"].endswith("send_email.json")
