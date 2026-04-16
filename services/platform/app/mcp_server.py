"""MCP server — implements tools/list and tools/call for FuseKit MCP transports."""

import uuid
from typing import Any

from mcp.server import Server
from mcp.types import TextContent, Tool
from sqlalchemy import select

from app.db import async_session
from app.models import ToolDefinition
from app.services.capabilities_service import (
    DEMO_USER_TOKEN,
    execute_capability,
    get_user_id_for_token,
    queue_missing_tool_integration,
)
from app.tools.registry import load_all

# Load all tool implementations on import
load_all()

mcp = Server("fusekit")

async def _get_demo_user_id() -> uuid.UUID:
    """Get the demo user's ID."""
    return await get_user_id_for_token(DEMO_USER_TOKEN)


async def _queue_missing_tool_integration(tool_name: str) -> None:
    """Create integration job for missing tools and forward to integrator."""
    await queue_missing_tool_integration(tool_name)


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
    result = await execute_capability(
        user_id=user_id,
        tool_name=name,
        arguments=arguments,
    )

    text = result.text
    if result.ok and result.balance_after is not None and result.balance_after < 500:
        text += f"\n\n⚠️ LOW BALANCE: {result.balance_after} credits remaining."

    return [TextContent(type="text", text=text)]
