"""Integration job helpers shared by API and MCP tool-miss handling."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from urllib.parse import quote

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import IntegrationJob

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class IntegrationForwardPayload:
    job_id: str
    docs_url: str
    requested_by: str
    requested_tool_name: str | None = None


def build_tool_miss_docs_url(tool_name: str) -> str:
    """Return a real HTTP search URL for an unknown MCP tool name.

    The integrator's discovery agent will fetch this page and infer the API
    from the search results, rather than receiving an unroutable mcp:// URI.
    """
    safe_name = quote(tool_name.strip().lower().replace("_", " ") or "unknown api")
    return f"https://www.google.com/search?q={safe_name}+API+documentation"


async def create_integration_job(
    session: AsyncSession,
    *,
    docs_url: str,
    requested_by: str,
    requested_tool_name: str | None = None,
) -> IntegrationJob:
    """Persist an integration job and return the freshly committed row."""
    job = IntegrationJob(
        docs_url=docs_url,
        requested_tool_name=requested_tool_name,
        status="queued",
        current_stage="queued",
        triggered_by=requested_by,
    )
    session.add(job)
    await session.commit()
    await session.refresh(job)
    return job


async def forward_job_to_integrator(payload: IntegrationForwardPayload) -> None:
    """Best-effort forward to integrator service; never raises."""
    body = {
        "job_id": payload.job_id,
        "docs_url": payload.docs_url,
        "requested_by": payload.requested_by,
        "requested_tool_name": payload.requested_tool_name,
    }
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            await client.post(f"{settings.integrator_url.rstrip('/')}/integrate", json=body)
    except Exception:
        logger.exception("Failed to forward integration job %s to integrator", payload.job_id)


def forward_job_non_blocking(payload: IntegrationForwardPayload) -> None:
    """Schedule async forwarding without blocking the current request."""
    try:
        asyncio.create_task(forward_job_to_integrator(payload))
    except RuntimeError:
        # If no running loop is available, run directly in a task-like way.
        # This only happens in edge test contexts.
        logger.warning("No active event loop for background forwarding; skipping job %s", payload.job_id)


def to_status_payload(job: IntegrationJob) -> dict[str, str | None]:
    """Serialize integration job status for API responses."""
    return {
        "job_id": str(job.id),
        "status": job.status,
        "current_stage": job.current_stage,
        "docs_url": job.docs_url,
        "requested_tool_name": job.requested_tool_name,
        "triggered_by": job.triggered_by,
        "error_log": job.error_log,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
    }
