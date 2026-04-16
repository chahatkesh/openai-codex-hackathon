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

STAGE_POLICIES = {
    "discovery": {
        "role_name": "discovery",
        "model": settings.discovery_model,
        "reasoning_effort": settings.discovery_reasoning_effort,
    },
    "reader": {
        "role_name": "reader",
        "model": settings.reader_model,
        "reasoning_effort": settings.reader_reasoning_effort,
    },
    "codegen": {
        "role_name": "codegen",
        "model": settings.codegen_model,
        "reasoning_effort": settings.codegen_reasoning_effort,
    },
    "test_fix": {
        "role_name": "test_fix",
        "model": settings.test_fix_model,
        "reasoning_effort": settings.test_fix_reasoning_effort,
    },
}


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


def build_stage_llms(api_key: str | None = None) -> dict[str, LLMClient]:
    return {
        stage: LLMClient(
            api_key=api_key,
            model=policy["model"],
            reasoning_effort=policy["reasoning_effort"],
            role_name=policy["role_name"],
        )
        for stage, policy in STAGE_POLICIES.items()
    }


def _get_stage_llm(
    stage: str,
    shared_llm: LLMClient | None,
    stage_llms: dict[str, LLMClient],
) -> LLMClient:
    if shared_llm is None:
        return stage_llms[stage]
    stage_client = getattr(shared_llm, "stage_client", None)
    if callable(stage_client):
        resolved = stage_client(stage)
        if resolved is not None:
            return resolved
    return shared_llm


async def execute_pipeline(context: PipelineContext, session_factory, llm: LLMClient | None = None) -> None:
    stage_llms = build_stage_llms()

    async with session_factory() as session:
        job = await _load_job(session, context.job_id)
        job.status = "running"
        await session.commit()

    try:
        with StageTimer("discovery", context.job_id):
            async with session_factory() as session:
                job = await _load_job(session, context.job_id)
                await _set_stage(session, job, "discovery")
            discovery = await run_discovery(
                context.docs_url,
                _get_stage_llm("discovery", llm, stage_llms),
            )

        with StageTimer("reader", context.job_id):
            async with session_factory() as session:
                job = await _load_job(session, context.job_id)
                await _set_stage(session, job, "reader")
            api_spec = await run_reader(
                context.docs_url,
                discovery,
                _get_stage_llm("reader", llm, stage_llms),
            )

        with StageTimer("codegen", context.job_id):
            async with session_factory() as session:
                job = await _load_job(session, context.job_id)
                await _set_stage(session, job, "codegen")
            generated = await run_codegen(
                api_spec,
                context.requested_tool_name,
                _get_stage_llm("codegen", llm, stage_llms),
            )

        with StageTimer("test_fix", context.job_id):
            async with session_factory() as session:
                job = await _load_job(session, context.job_id)
                await _set_stage(session, job, "test_fix")
            test_result = await run_test_fix(
                generated,
                _get_stage_llm("test_fix", llm, stage_llms),
                settings.max_fix_attempts,
            )

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
