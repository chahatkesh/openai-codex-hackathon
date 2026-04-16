"""request_integration — Queue a new capability/tool integration job."""

from __future__ import annotations

import json

from sqlalchemy import select

from app.db import async_session
from app.models import ToolDefinition
from app.services.integrations_service import (
    IntegrationForwardPayload,
    build_discovery_docs_url,
    create_integration_job,
    forward_job_non_blocking,
)
from app.services.manifest_service import build_manifest_pointer, load_manifest
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
    if requested_tool_name:
        async with async_session() as session:
            result = await session.execute(
                select(ToolDefinition).where(
                    ToolDefinition.name == requested_tool_name,
                    ToolDefinition.status == "live",
                )
            )
            existing = result.scalar_one_or_none()
            if existing is not None:
                manifest = load_manifest(existing)
                return json.dumps(
                    {
                        "status": "already_available",
                        "message": f"Tool '{requested_tool_name}' is already live.",
                        "manifest": manifest,
                        "pointer": build_manifest_pointer(requested_tool_name),
                    },
                    indent=2,
                )

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
    return json.dumps(
        {
            "status": "integration_requested",
            "message": (
                f"Integration requested for '{requested_label}'. "
                "FuseKit will attempt discovery, code generation, testing, and publish."
            ),
            "job_id": str(job.id),
            "docs_url": job.docs_url,
            "requested_tool_name": job.requested_tool_name,
        },
        indent=2,
    )


registry.register("request_integration", execute)
