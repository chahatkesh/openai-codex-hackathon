from __future__ import annotations

import asyncio
import uuid

import pytest


@pytest.mark.asyncio
async def test_integrate_enqueues_and_get_status(api_client, session_factory, seeded_job, monkeypatch):
    from app import main as main_module

    async def fake_execute_pipeline(_context, _session_factory, llm=None):  # noqa: ARG001
        return None

    monkeypatch.setattr(main_module, "execute_pipeline", fake_execute_pipeline)
    monkeypatch.setattr(main_module, "SessionLocal", session_factory)

    response = await api_client.post(
        "/integrate",
        json={
            "job_id": str(seeded_job.id),
            "docs_url": "https://example.com/docs",
            "requested_by": "user",
            "requested_tool_name": "example_tool",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "queued"

    await asyncio.sleep(0)

    status_response = await api_client.get(f"/integrate/{seeded_job.id}")
    assert status_response.status_code == 200
    payload = status_response.json()
    assert payload["job_id"] == str(seeded_job.id)
    assert payload["status"] in {"queued", "running", "complete", "failed"}


@pytest.mark.asyncio
async def test_integrate_404_when_job_missing(api_client):
    missing_id = uuid.uuid4()
    response = await api_client.post(
        "/integrate",
        json={
            "job_id": str(missing_id),
            "docs_url": "https://example.com/docs",
            "requested_by": "user",
        },
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_integrate_validation_error(api_client, seeded_job):
    response = await api_client.post(
        "/integrate",
        json={
            "job_id": str(seeded_job.id),
            "requested_by": "user",
        },
    )
    assert response.status_code == 422
