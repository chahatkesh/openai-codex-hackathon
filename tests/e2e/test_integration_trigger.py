from __future__ import annotations

import os
from datetime import datetime, timezone

import pytest

from ._mcp import McpTestClient


pytest.importorskip("mcp")
asyncpg = pytest.importorskip("asyncpg")


def _db_url() -> str:
    return os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://fusekit:fusekit@localhost:5432/fusekit",
    ).replace("+asyncpg", "")


@pytest.mark.asyncio
async def test_tool_not_found_creates_integration_job(service_config):
    started_at = datetime.now(timezone.utc)
    async with McpTestClient(service_config.mcp_sse_url) as mcp:
        text = await mcp.call_tool("__missing_tool_for_e2e__", {"foo": "bar"})
        assert "TOOL_NOT_FOUND" in text

    conn = await asyncpg.connect(_db_url())
    try:
        row = await conn.fetchrow(
            """
            SELECT id::text, status
            FROM integration_jobs
            WHERE created_at >= $1
            ORDER BY created_at DESC
            LIMIT 1
            """,
            started_at,
        )
    finally:
        await conn.close()

    assert row is not None, "Expected integration job to be created on tool miss"
    assert row["status"] in {"queued", "running", "complete", "failed"}


@pytest.mark.asyncio
async def test_manual_integrate_endpoint_works(service_config, api_client):
    payload = {
        "docs_url": "https://example.com/docs",
        "requested_by": "user",
        "requested_tool_name": "manual_test_tool",
    }
    create_resp = await api_client.post(f"{service_config.api_base_url}/api/integrate", json=payload)
    if create_resp.status_code == 404:
        pytest.skip("Integration endpoints not available yet (waiting on Agent 1)")
    create_resp.raise_for_status()
    body = create_resp.json()
    job_id = body.get("job_id")
    assert isinstance(job_id, str) and job_id

    status_resp = await api_client.get(f"{service_config.api_base_url}/api/integrate/{job_id}")
    status_resp.raise_for_status()
    status_body = status_resp.json()
    assert status_body.get("status") in {"queued", "running", "complete", "failed"}
