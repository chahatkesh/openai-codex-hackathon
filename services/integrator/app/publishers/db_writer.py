from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import IntegrationJob, ToolDefinition
from app.schemas import GeneratedTool, TestResult

logger = logging.getLogger("fusekit.integrator.publisher")

# Must match DYNAMIC_TOOLS_DIR in services/platform/app/tools/registry.py
DYNAMIC_TOOLS_DIR = Path("/tmp/fusekit_dynamic_tools")


async def publish_tool(
    session: AsyncSession,
    job: IntegrationJob,
    generated: GeneratedTool,
    test_result: TestResult,
) -> ToolDefinition | None:
    if not test_result.success:
        job.status = "failed"
        job.error_log = (test_result.error_log or "Tool validation failed")[:2000]
        job.completed_at = datetime.now(timezone.utc)
        await session.commit()
        return None

    existing = await session.execute(
        select(ToolDefinition).where(ToolDefinition.name == generated.name)
    )
    tool = existing.scalar_one_or_none()
    if tool is None:
        tool = ToolDefinition(
            name=generated.name,
            description=generated.description,
            provider=generated.provider,
            cost_per_call=generated.cost_per_call,
            status=generated.status,
            input_schema=generated.input_schema,
            output_schema=generated.output_schema,
            category=generated.category,
            source="pipeline",
            version=generated.version,
            implementation_module=generated.implementation_module,
        )
        session.add(tool)
        await session.flush()
    else:
        tool.description = generated.description
        tool.provider = generated.provider
        tool.cost_per_call = generated.cost_per_call
        tool.status = generated.status
        tool.input_schema = generated.input_schema
        tool.output_schema = generated.output_schema
        tool.category = generated.category
        tool.source = "pipeline"
        tool.version = generated.version
        tool.implementation_module = generated.implementation_module

    job.status = "complete"
    job.current_stage = "publish"
    job.resulting_tool_id = tool.id
    job.error_log = None
    job.completed_at = datetime.now(timezone.utc)

    await session.commit()

    # Write python_code to shared dynamic-tools directory so the platform
    # registry can load and execute it without a container restart.
    try:
        DYNAMIC_TOOLS_DIR.mkdir(parents=True, exist_ok=True)
        tool_file = DYNAMIC_TOOLS_DIR / f"{tool.name}.py"
        tool_file.write_text(generated.python_code, encoding="utf-8")
        logger.info("dynamic_tool_written name=%s path=%s", tool.name, tool_file)
    except Exception as exc:
        # Non-fatal — tool is in DB, platform will surface a clear error
        logger.error("dynamic_tool_write_failed name=%s error=%s", tool.name, exc)

    return tool
