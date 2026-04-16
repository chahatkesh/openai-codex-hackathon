from __future__ import annotations

import pytest
from sqlalchemy import select

from app.models import IntegrationJob, ToolDefinition
from app.pipeline import execute_pipeline
from app.schemas import APISpecification, DiscoveryResult, GeneratedTool, PipelineContext, TestResult


class StubLLM:
    async def generate_json(self, _system_prompt: str, _user_prompt: str):
        return {}


@pytest.mark.asyncio
async def test_pipeline_marks_job_complete(monkeypatch, session_factory, seeded_job):
    async def fake_discovery(_docs_url, _llm):
        return DiscoveryResult(provider_name="Example", auth_method="none")

    async def fake_reader(_docs_url, _discovery, _llm):
        return APISpecification(provider_name="Example", endpoints=[])

    async def fake_codegen(_api_spec, requested_tool_name, _llm):
        return GeneratedTool(
            name=requested_tool_name or "example_tool",
            description="Generated",
            provider="Example",
            input_schema={"type": "object", "properties": {}},
            output_schema={"type": "object", "properties": {"ok": {"type": "boolean"}}},
            implementation_module="app.tools.example_tool.execute",
            python_code="async def execute(**kwargs) -> str:\n    return 'ok'\n",
        )

    async def fake_test_fix(_generated, _llm, _max_attempts):
        return TestResult(success=True, final_code="async def execute(**kwargs): return 'ok'", attempts=1)

    monkeypatch.setattr("app.pipeline.run_discovery", fake_discovery)
    monkeypatch.setattr("app.pipeline.run_reader", fake_reader)
    monkeypatch.setattr("app.pipeline.run_codegen", fake_codegen)
    monkeypatch.setattr("app.pipeline.run_test_fix", fake_test_fix)

    context = PipelineContext(
        job_id=seeded_job.id,
        docs_url=seeded_job.docs_url,
        requested_by=seeded_job.triggered_by,
        requested_tool_name=seeded_job.requested_tool_name,
    )

    await execute_pipeline(context, session_factory, llm=StubLLM())

    async with session_factory() as session:
        job_result = await session.execute(
            select(IntegrationJob).where(IntegrationJob.id == seeded_job.id)
        )
        job = job_result.scalar_one()

        assert job.status == "complete"
        assert job.current_stage == "publish"
        assert job.completed_at is not None

        tool_result = await session.execute(
            select(ToolDefinition).where(ToolDefinition.name == seeded_job.requested_tool_name)
        )
        tool = tool_result.scalar_one_or_none()
        assert tool is not None
        assert tool.source == "pipeline"
