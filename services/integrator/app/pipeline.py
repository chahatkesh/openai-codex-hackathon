from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.codegen import run_codegen
from app.agents.discovery import run_discovery
from app.agents.reader import run_reader
from app.agents.test_fix import run_test_fix
from app.config import settings
from app.llm import LLMClient
from app.logging_utils import StageTimer, logger
from app.models import IntegrationJob
from app.publishers.db_writer import publish_tool
from app.schemas import PipelineContext


def _trim_error(exc: Exception) -> str:
    return str(exc).strip()[:2000]


async def _load_job(session: AsyncSession, job_id: UUID) -> IntegrationJob:
    result = await session.execute(select(IntegrationJob).where(IntegrationJob.id == job_id))
    job = result.scalar_one_or_none()
    if job is None:
        raise ValueError(f"Integration job {job_id} not found")
    return job


async def _set_stage(session: AsyncSession, job: IntegrationJob, stage: str) -> None:
    job.current_stage = stage
    job.status = "running"
    job.attempts = (job.attempts or 0) + 1
    await session.commit()


async def execute_pipeline(context: PipelineContext, session_factory, llm: LLMClient | None = None) -> None:
    llm_client = llm or LLMClient()

    async with session_factory() as session:
        job = await _load_job(session, context.job_id)
        job.status = "running"
        await session.commit()

    try:
        with StageTimer("discovery", context.job_id):
            async with session_factory() as session:
                job = await _load_job(session, context.job_id)
                await _set_stage(session, job, "discovery")
            discovery = await run_discovery(context.docs_url, llm_client)

        with StageTimer("reader", context.job_id):
            async with session_factory() as session:
                job = await _load_job(session, context.job_id)
                await _set_stage(session, job, "reader")
            api_spec = await run_reader(context.docs_url, discovery, llm_client)

        with StageTimer("codegen", context.job_id):
            async with session_factory() as session:
                job = await _load_job(session, context.job_id)
                await _set_stage(session, job, "codegen")
            generated = await run_codegen(api_spec, context.requested_tool_name, llm_client)

        with StageTimer("test_fix", context.job_id):
            async with session_factory() as session:
                job = await _load_job(session, context.job_id)
                await _set_stage(session, job, "test_fix")
            test_result = await run_test_fix(generated, llm_client, settings.max_fix_attempts)

        with StageTimer("publish", context.job_id):
            async with session_factory() as session:
                job = await _load_job(session, context.job_id)
                job.current_stage = "publish"
                await session.commit()
                await publish_tool(
                    session,
                    job,
                    generated,
                    test_result,
                    discovery=discovery,
                    api_spec=api_spec,
                )

    except Exception as exc:
        logger.exception("pipeline_failed job_id=%s", context.job_id)
        async with session_factory() as session:
            try:
                job = await _load_job(session, context.job_id)
                job.status = "failed"
                job.error_log = _trim_error(exc)
                job.completed_at = datetime.now(timezone.utc)
                await session.commit()
            except Exception:
                logger.exception("pipeline_failure_persist_failed job_id=%s", context.job_id)
