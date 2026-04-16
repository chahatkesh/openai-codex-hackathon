from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from fastapi import HTTPException

from app.api.integrations import IntegrateRequest, get_integration_job, trigger_integration
from app.models import IntegrationJob
from tests.helpers import DummyResult, FakeSession


@pytest.mark.asyncio
async def test_trigger_integration_creates_job_and_returns_queued(monkeypatch):
    job = IntegrationJob(
        id=uuid.uuid4(),
        docs_url="https://example.com/docs",
        requested_tool_name="send_slack_message",
        status="queued",
        current_stage="queued",
        attempts=0,
        error_log=None,
        resulting_tool_id=None,
        triggered_by="user",
        created_at=datetime.now(timezone.utc),
        completed_at=None,
    )

    async def fake_create(*_args, **_kwargs):
        return job

    forwarded = {}

    def fake_forward(payload):
        forwarded["job_id"] = payload.job_id

    monkeypatch.setattr("app.api.integrations.create_integration_job", fake_create)
    monkeypatch.setattr("app.api.integrations.forward_job_non_blocking", fake_forward)

    payload = await trigger_integration(
        request=IntegrateRequest(docs_url="https://example.com/docs", requested_tool_name="send_slack_message"),
        session=FakeSession(),
    )

    assert payload["status"] == "queued"
    assert payload["job_id"] == str(job.id)
    assert forwarded["job_id"] == str(job.id)


@pytest.mark.asyncio
async def test_get_integration_job_returns_status_payload():
    job_id = uuid.uuid4()
    job = IntegrationJob(
        id=job_id,
        docs_url="https://example.com/docs",
        requested_tool_name="send_slack_message",
        status="running",
        current_stage="codegen",
        attempts=1,
        error_log=None,
        resulting_tool_id=None,
        triggered_by="user",
        created_at=datetime.now(timezone.utc),
        completed_at=None,
    )
    session = FakeSession(execute_results=[DummyResult(job)])

    payload = await get_integration_job(job_id=job_id, session=session)

    assert payload["job_id"] == str(job_id)
    assert payload["status"] == "running"


@pytest.mark.asyncio
async def test_get_integration_job_404_when_missing():
    session = FakeSession(execute_results=[DummyResult(None)])

    with pytest.raises(HTTPException) as exc:
        await get_integration_job(job_id=uuid.uuid4(), session=session)

    assert exc.value.status_code == 404
