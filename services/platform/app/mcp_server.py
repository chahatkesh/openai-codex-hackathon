"""MCP server — implements tools/list and tools/call for FuseKit MCP transports."""

import time
import uuid
from typing import Any

from mcp.server import Server
from mcp.types import TextContent, Tool
from sqlalchemy import select

from app.db import async_session
from app.models import IntegrationJob, ToolCallLog, ToolDefinition, User
from app.services.integrations_service import (
    IntegrationForwardPayload,
    build_tool_miss_docs_url,
    forward_job_non_blocking,
)
from app.services.wallet_service import InsufficientFundsError, check_and_deduct, refund
from app.tools.registry import get_executor, load_all, load_dynamic

# Load all tool implementations on import
load_all()

mcp = Server("fusekit")

# For the hackathon demo, we use a single demo user
DEMO_USER_TOKEN = "demo-token-fusekit-2026"


async def _get_demo_user_id() -> uuid.UUID:
    """Get the demo user's ID."""
    async with async_session() as session:
        result = await session.execute(
            select(User.id).where(User.mcp_auth_token == DEMO_USER_TOKEN)
        )
        user_id = result.scalar_one_or_none()
        if not user_id:
            raise RuntimeError("Demo user not found. Run the seed script first.")
        return user_id


async def _queue_missing_tool_integration(tool_name: str) -> None:
    """Create integration job for missing tools and forward to integrator."""
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


@mcp.list_tools()
async def list_tools() -> list[Tool]:
    """Return all active tools from the database."""
    async with async_session() as session:
        result = await session.execute(
            select(ToolDefinition).where(ToolDefinition.status == "live")
        )
        tools = result.scalars().all()

    return [
        Tool(
            name=t.name,
            description=t.description,
            inputSchema=t.input_schema,
        )
        for t in tools
    ]


@mcp.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Execute a tool: auth → wallet check → execute → log."""
    user_id = await _get_demo_user_id()

    # Look up tool definition
    async with async_session() as session:
        result = await session.execute(
            select(ToolDefinition).where(
                ToolDefinition.name == name,
                ToolDefinition.status == "live",
            )
        )
        tool_def = result.scalar_one_or_none()

    if tool_def is None:
        await _queue_missing_tool_integration(name)

        return [
            TextContent(
                type="text",
                text=f"TOOL_NOT_FOUND: '{name}' is not in the catalog. "
                "An integration job has been queued. Retry in a few minutes.",
            )
        ]

    # Wallet check & deduct
    try:
        async with async_session() as session:
            new_balance = await check_and_deduct(
                session, user_id, name, tool_def.cost_per_call
            )
    except InsufficientFundsError as e:
        return [
            TextContent(
                type="text",
                text=f"INSUFFICIENT_FUNDS: Your wallet balance is {e.balance} credits. "
                f"This tool costs {e.cost} credits. Please top up at the marketplace.",
            )
        ]

    # Execute the tool — try static registry first, then dynamic (pipeline-generated)
    executor = get_executor(name)
    if executor is None:
        executor = load_dynamic(name)
    if executor is None:
        # Refund since we can't execute
        async with async_session() as session:
            await refund(session, user_id, name, tool_def.cost_per_call)
        return [
            TextContent(
                type="text",
                text=f"EXECUTION_ERROR: Tool '{name}' is registered but has no implementation.",
            )
        ]

    start = time.monotonic()
    try:
        result_text = await executor(**arguments)
        duration_ms = int((time.monotonic() - start) * 1000)

        # Log successful call
        async with async_session() as session:
            log = ToolCallLog(
                user_id=user_id,
                tool_name=name,
                input_args=arguments,
                result_status="success",
                credits_deducted=tool_def.cost_per_call,
                execution_duration_ms=duration_ms,
            )
            session.add(log)
            await session.commit()

        # Low balance warning
        warning = ""
        if new_balance < 500:
            warning = f"\n\n⚠️ LOW BALANCE: {new_balance} credits remaining."

        return [TextContent(type="text", text=result_text + warning)]

    except Exception as e:
        duration_ms = int((time.monotonic() - start) * 1000)

        # Refund on failure
        async with async_session() as session:
            await refund(session, user_id, name, tool_def.cost_per_call)

        # Log failed call
        async with async_session() as session:
            log = ToolCallLog(
                user_id=user_id,
                tool_name=name,
                input_args=arguments,
                result_status="error",
                error_message=str(e)[:1000],
                credits_deducted=0,
                execution_duration_ms=duration_ms,
            )
            session.add(log)
            await session.commit()

        return [
            TextContent(
                type="text",
                text=f"EXECUTION_ERROR: {e}",
            )
        ]
