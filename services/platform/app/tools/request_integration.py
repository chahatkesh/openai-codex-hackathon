"""request_integration — Queue a new capability/tool integration job."""

from __future__ import annotations

from app.db import async_session
from app.services.integrations_service import (
    IntegrationForwardPayload,
    build_discovery_docs_url,
    create_integration_job,
    forward_job_non_blocking,
)
from app.tools import registry


async def execute(
    capability_description: str,
    docs_url: str | None = None,
    requested_tool_name: str | None = None,
) -> str:
    """Queue an integration job for a missing capability.

    This is the generic fallback tool Codex should call when the desired
    provider/capability is not already exposed in the FuseKit catalog.
    """
    discovery_url = docs_url or build_discovery_docs_url(
        requested_tool_name or capability_description
    )

    async with async_session() as session:
        job = await create_integration_job(
            session,
            docs_url=discovery_url,
            requested_by="user",
            requested_tool_name=requested_tool_name,
        )

    forward_job_non_blocking(
        IntegrationForwardPayload(
            job_id=str(job.id),
            docs_url=job.docs_url,
            requested_by=job.triggered_by,
            requested_tool_name=job.requested_tool_name,
        )
    )

    requested_label = requested_tool_name or capability_description
    return (
        f"Integration requested for '{requested_label}'. "
        f"Job ID: {job.id}. "
        f"Discovery URL: {job.docs_url}. "
        "FuseKit will attempt discovery, code generation, testing, and publish."
    )


registry.register("request_integration", execute)
