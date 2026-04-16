"""Capability manifests and shared execution flow for FuseKit."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from typing import Any

from sqlalchemy import select

from app.db import async_session
from app.models import IntegrationJob, ToolCallLog, ToolDefinition, User
from app.services.integrations_service import (
    IntegrationForwardPayload,
    build_tool_miss_docs_url,
    forward_job_non_blocking,
)
from app.services.wallet_service import InsufficientFundsError, check_and_deduct, refund
from app.tools.registry import get_executor, load_dynamic

DEMO_USER_TOKEN = "demo-token-fusekit-2026"


@dataclass(slots=True)
class ExecutionResult:
    ok: bool
    tool_name: str
    text: str
    is_error: bool = False
    error_code: str | None = None
    balance_after: int | None = None


async def get_user_id_for_token(auth_token: str = DEMO_USER_TOKEN) -> uuid.UUID:
    """Resolve a FuseKit user from an auth token."""
    async with async_session() as session:
        result = await session.execute(
            select(User.id).where(User.mcp_auth_token == auth_token)
        )
        user_id = result.scalar_one_or_none()
        if not user_id:
            raise RuntimeError("Demo user not found. Run the seed script first.")
        return user_id


async def get_tool_definition(tool_name: str) -> ToolDefinition | None:
    async with async_session() as session:
        result = await session.execute(
            select(ToolDefinition).where(
                ToolDefinition.name == tool_name,
                ToolDefinition.status == "live",
            )
        )
        return result.scalar_one_or_none()


def _build_example_request(schema: dict[str, Any]) -> dict[str, Any]:
    properties = schema.get("properties", {})
    required = schema.get("required", [])
    example: dict[str, Any] = {}

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


def build_capability_manifest(tool: ToolDefinition) -> dict[str, Any]:
    """Build the runtime contract UFC can use to wire a deployed app."""
    return {
        "name": tool.name,
        "description": tool.description,
        "provider": tool.provider,
        "runtime_endpoint": {
            "method": "POST",
            "path": f"/api/execute/{tool.name}",
        },
        "input_schema": tool.input_schema,
        "output_schema": tool.output_schema,
        "billing": {
            "cost_per_call": tool.cost_per_call,
            "currency": "credits",
        },
        "auth": {
            "type": "bearer",
            "header": "Authorization",
            "format": "Bearer <fusekit_token>",
        },
        "example_request": _build_example_request(tool.input_schema),
    }


async def queue_missing_tool_integration(tool_name: str) -> None:
    """Create an integration job for a missing tool and forward it."""
    async with async_session() as session:
        missing_job = IntegrationJob(
            docs_url=build_tool_miss_docs_url(tool_name),
            requested_tool_name=tool_name,
            status="queued",
            current_stage="queued",
            triggered_by="mcp_tool_miss",
        )
        session.add(missing_job)
        await session.commit()
        await session.refresh(missing_job)

    forward_job_non_blocking(
        IntegrationForwardPayload(
            job_id=str(missing_job.id),
            docs_url=missing_job.docs_url,
            requested_by=missing_job.triggered_by,
            requested_tool_name=missing_job.requested_tool_name,
        )
    )


async def execute_capability(
    *,
    user_id: uuid.UUID,
    tool_name: str,
    arguments: dict[str, Any],
) -> ExecutionResult:
    """Shared capability execution used by both MCP and HTTP surfaces."""
    tool_def = await get_tool_definition(tool_name)
    if tool_def is None:
        await queue_missing_tool_integration(tool_name)
        return ExecutionResult(
            ok=False,
            tool_name=tool_name,
            text=(
                f"TOOL_NOT_FOUND: '{tool_name}' is not in the catalog. "
                "An integration job has been queued. Retry in a few minutes."
            ),
            is_error=True,
            error_code="TOOL_NOT_FOUND",
        )

    try:
        async with async_session() as session:
            new_balance = await check_and_deduct(
                session, user_id, tool_name, tool_def.cost_per_call
            )
    except InsufficientFundsError as exc:
        return ExecutionResult(
            ok=False,
            tool_name=tool_name,
            text=(
                f"INSUFFICIENT_FUNDS: Your wallet balance is {exc.balance} credits. "
                f"This tool costs {exc.cost} credits. Please top up at the marketplace."
            ),
            is_error=True,
            error_code="INSUFFICIENT_FUNDS",
        )

    executor = get_executor(tool_name)
    if executor is None:
        executor = load_dynamic(tool_name)
    if executor is None:
        async with async_session() as session:
            await refund(session, user_id, tool_name, tool_def.cost_per_call)
        return ExecutionResult(
            ok=False,
            tool_name=tool_name,
            text=f"EXECUTION_ERROR: Tool '{tool_name}' is registered but has no implementation.",
            is_error=True,
            error_code="EXECUTION_ERROR",
        )

    start = time.monotonic()
    try:
        result_text = await executor(**arguments)
        duration_ms = int((time.monotonic() - start) * 1000)

        async with async_session() as session:
            log = ToolCallLog(
                user_id=user_id,
                tool_name=tool_name,
                input_args=arguments,
                result_status="success",
                credits_deducted=tool_def.cost_per_call,
                execution_duration_ms=duration_ms,
            )
            session.add(log)
            await session.commit()

        return ExecutionResult(
            ok=True,
            tool_name=tool_name,
            text=result_text,
            balance_after=new_balance,
        )
    except Exception as exc:
        duration_ms = int((time.monotonic() - start) * 1000)

        async with async_session() as session:
            await refund(session, user_id, tool_name, tool_def.cost_per_call)

        async with async_session() as session:
            log = ToolCallLog(
                user_id=user_id,
                tool_name=tool_name,
                input_args=arguments,
                result_status="error",
                error_message=str(exc)[:1000],
                credits_deducted=0,
                execution_duration_ms=duration_ms,
            )
            session.add(log)
            await session.commit()

        return ExecutionResult(
            ok=False,
            tool_name=tool_name,
            text=f"EXECUTION_ERROR: {exc}",
            is_error=True,
            error_code="EXECUTION_ERROR",
        )
