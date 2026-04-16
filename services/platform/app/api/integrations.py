"""Integrations API routes — /api/integrate."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, HttpUrl
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.models import IntegrationJob
from app.services.integrations_service import (
    IntegrationForwardPayload,
    create_integration_job,
    forward_job_non_blocking,
    to_status_payload,
)

router = APIRouter(prefix="/api/integrate", tags=["integrations"])


@router.get("")
async def list_recent_jobs(
    limit: int = 20,
    session: AsyncSession = Depends(get_session),
):
    """Return recent integration jobs ordered by creation time (newest first)."""
    effective_limit = max(1, min(limit, 100))
    result = await session.execute(
        select(IntegrationJob)
        .order_by(IntegrationJob.created_at.desc())
        .limit(effective_limit)
    )
    jobs = result.scalars().all()
    return [to_status_payload(j) for j in jobs]


class IntegrateRequest(BaseModel):
    docs_url: HttpUrl
    requested_by: str = "user"
    requested_tool_name: str | None = None


@router.post("")
async def trigger_integration(
    request: IntegrateRequest,
    session: AsyncSession = Depends(get_session),
):
    """Create an integration job and forward to the integrator service."""
    job = await create_integration_job(
        session,
        docs_url=str(request.docs_url),
        requested_by=request.requested_by,
        requested_tool_name=request.requested_tool_name,
    )

    forward_job_non_blocking(
        IntegrationForwardPayload(
            job_id=str(job.id),
            docs_url=job.docs_url,
            requested_by=job.triggered_by,
            requested_tool_name=job.requested_tool_name,
        )
    )

    return {
        "job_id": str(job.id),
        "status": job.status,
    }


@router.get("/{job_id}")
async def get_integration_job(
    job_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    """Get the status of an integration job by ID."""
    result = await session.execute(select(IntegrationJob).where(IntegrationJob.id == job_id))
    job = result.scalar_one_or_none()
    if job is None:
        raise HTTPException(status_code=404, detail="Integration job not found")

    return to_status_payload(job)
