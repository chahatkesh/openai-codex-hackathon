from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from uuid import UUID

import uvicorn
from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db import SessionLocal, check_db_connection, get_session
from app.models import IntegrationJob
from app.pipeline import execute_pipeline
from app.schemas import IntegrateRequest, IntegrateResponse, JobStatusResponse, PipelineContext

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("fusekit.integrator")


@asynccontextmanager
async def lifespan(app: FastAPI):
    startup_errors: list[str] = []

    if not settings.openai_api_key:
        startup_errors.append("OPENAI_API_KEY missing")

    db_ok, db_error = await check_db_connection()
    if not db_ok:
        startup_errors.append(f"database_unreachable: {db_error}")

    app.state.startup_errors = startup_errors
    if startup_errors:
        logger.warning("integrator_startup_degraded errors=%s", startup_errors)
    else:
        logger.info("integrator_startup_ok")

    app.state.tasks = set()
    yield

    tasks = list(app.state.tasks)
    for task in tasks:
        if not task.done():
            task.cancel()
    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)


app = FastAPI(title="FuseKit Integrator", version="0.1.0", lifespan=lifespan)


@app.get("/health")
async def health():
    errors = getattr(app.state, "startup_errors", [])
    status_value = "ok" if not errors else "degraded"
    return {
        "status": status_value,
        "service": "fusekit-integrator",
        "errors": errors,
    }


@app.post("/integrate", response_model=IntegrateResponse)
async def integrate(
    payload: IntegrateRequest,
    session: AsyncSession = Depends(get_session),
):
    startup_errors = getattr(app.state, "startup_errors", [])
    if startup_errors:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"message": "Integrator unhealthy", "errors": startup_errors},
        )

    result = await session.execute(select(IntegrationJob).where(IntegrationJob.id == payload.job_id))
    job = result.scalar_one_or_none()
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {payload.job_id} not found in platform DB",
        )

    job.docs_url = str(payload.docs_url)
    job.requested_tool_name = payload.requested_tool_name
    job.triggered_by = payload.requested_by
    job.status = "queued"
    job.current_stage = "queued"
    job.error_log = None
    await session.commit()

    context = PipelineContext(
        job_id=payload.job_id,
        docs_url=str(payload.docs_url),
        requested_by=payload.requested_by,
        requested_tool_name=payload.requested_tool_name,
    )

    task = asyncio.create_task(execute_pipeline(context, SessionLocal), name=f"integration-{payload.job_id}")
    app.state.tasks.add(task)
    task.add_done_callback(app.state.tasks.discard)

    return IntegrateResponse(job_id=payload.job_id, status="queued")


@app.get("/integrate/{job_id}", response_model=JobStatusResponse)
async def get_job_status(
    job_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(select(IntegrationJob).where(IntegrationJob.id == job_id))
    job = result.scalar_one_or_none()
    if job is None:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    return JobStatusResponse(
        job_id=job.id,
        status=job.status,
        current_stage=job.current_stage,
        attempts=job.attempts,
        error_log=job.error_log,
        resulting_tool_id=job.resulting_tool_id,
        requested_tool_name=job.requested_tool_name,
        docs_url=job.docs_url,
        created_at=job.created_at,
        completed_at=job.completed_at,
    )


def main() -> None:
    uvicorn.run("app.main:app", host="0.0.0.0", port=8001, reload=True)


if __name__ == "__main__":
    main()
