from __future__ import annotations

import logging
import json
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import IntegrationJob, ToolDefinition
from app.services.artifact_store import (
    artifact_key_for_manifest,
    artifact_key_for_module,
    artifact_uri_for_key,
    upload_text,
)
from app.schemas import APISpecification, DiscoveryResult, GeneratedTool, TestResult

logger = logging.getLogger("fusekit.integrator.publisher")

# Must match DYNAMIC_TOOLS_DIR in services/platform/app/tools/registry.py
DYNAMIC_TOOLS_DIR = Path("/tmp/fusekit_dynamic_tools")
MANIFESTS_DIR = DYNAMIC_TOOLS_DIR / "manifests"


def _build_example_request(schema: dict) -> dict:
    properties = schema.get("properties", {})
    required = schema.get("required", [])
    example: dict = {}

    for field in required:
        prop = properties.get(field, {})
        if "default" in prop:
            example[field] = prop["default"]
            continue
        prop_type = prop.get("type")
        if prop_type == "string":
            if "url" in field:
                example[field] = "https://example.com"
            elif "email" in field or field == "to":
                example[field] = "demo@example.com"
            elif "phone" in field:
                example[field] = "+10000000000"
            else:
                example[field] = "example"
        elif prop_type == "integer":
            example[field] = 1
        elif prop_type == "boolean":
            example[field] = False
        elif prop_type == "array":
            example[field] = []
        elif prop_type == "object":
            example[field] = {}
        else:
            example[field] = "example"

    return example


def _manifest_payload(
    job: IntegrationJob,
    generated: GeneratedTool,
    test_result: TestResult,
    discovery: DiscoveryResult,
    api_spec: APISpecification,
    tool: ToolDefinition,
) -> dict:
    platform_api_url = settings.platform_api_url.rstrip("/")
    runtime_path = f"/api/execute/{tool.name}"
    manifest_http_path = f"/api/capabilities/{tool.name}/manifest"
    return {
        "tool_name": tool.name,
        "name": tool.name,
        "provider": generated.provider,
        "status": generated.status,
        "category": generated.category,
        "source": "pipeline",
        "version": generated.version,
        "description": generated.description,
        "base_url": platform_api_url,
        "runtime_endpoint": {
            "method": "POST",
            "path": runtime_path,
            "url": f"{platform_api_url}{runtime_path}",
        },
        "billing": {
            "cost_per_call": tool.cost_per_call,
            "currency": "credits",
        },
        "auth": {
            "type": "bearer",
            "header": "Authorization",
            "format": "Bearer <fusekit_token>",
            "token_env_var": "FUSEKIT_TOKEN",
            "local_development_token": "demo-token-fusekit-2026",
        },
        "example_request": _build_example_request(tool.input_schema),
        "manifest_endpoint": {
            "method": "GET",
            "path": manifest_http_path,
            "url": f"{platform_api_url}{manifest_http_path}",
        },
        "manifest_pointer": {
            "tool_name": tool.name,
            "manifest_path": str(MANIFESTS_DIR / f"{tool.name}.json"),
            "artifact_key": artifact_key_for_manifest(tool.name),
            "artifact_uri": artifact_uri_for_key(artifact_key_for_manifest(tool.name)),
            "http_path": manifest_http_path,
            "http_url": f"{platform_api_url}{manifest_http_path}",
        },
        "input_schema": tool.input_schema,
        "output_schema": tool.output_schema,
        "implementation_module": tool.implementation_module,
        "docs_url": job.docs_url,
        "integration_job": {
            "job_id": str(job.id),
            "triggered_by": job.triggered_by,
            "requested_tool_name": job.requested_tool_name,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        },
        "discovery": discovery.model_dump(),
        "api_spec": api_spec.model_dump(),
        "tool_definition": {
            "id": str(tool.id),
            "cost_per_call": tool.cost_per_call,
            "input_schema": tool.input_schema,
            "output_schema": tool.output_schema,
            "implementation_module": tool.implementation_module,
        },
        "runtime_artifacts": {
            "python_module_path": str(DYNAMIC_TOOLS_DIR / f"{tool.name}.py"),
            "manifest_path": str(MANIFESTS_DIR / f"{tool.name}.json"),
            "python_module_key": artifact_key_for_module(tool.name),
            "manifest_key": artifact_key_for_manifest(tool.name),
            "python_module_uri": artifact_uri_for_key(artifact_key_for_module(tool.name)),
            "manifest_uri": artifact_uri_for_key(artifact_key_for_manifest(tool.name)),
        },
        "test_result": {
            "success": test_result.success,
            "attempts": test_result.attempts,
            "error_log": test_result.error_log,
        },
    }


async def publish_tool(
    session: AsyncSession,
    job: IntegrationJob,
    generated: GeneratedTool,
    test_result: TestResult,
    *,
    discovery: DiscoveryResult,
    api_spec: APISpecification,
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

        MANIFESTS_DIR.mkdir(parents=True, exist_ok=True)
        manifest = _manifest_payload(job, generated, test_result, discovery, api_spec, tool)
        manifest_file = MANIFESTS_DIR / f"{tool.name}.json"
        manifest_file.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        logger.info("dynamic_manifest_written name=%s path=%s", tool.name, manifest_file)

        upload_text(
            artifact_key_for_module(tool.name),
            generated.python_code,
            "text/x-python",
        )
        upload_text(
            artifact_key_for_manifest(tool.name),
            json.dumps(manifest, indent=2),
            "application/json",
        )
    except Exception as exc:
        # Non-fatal — tool is in DB, platform will surface a clear error
        logger.error("dynamic_artifact_write_failed name=%s error=%s", tool.name, exc)

    return tool
