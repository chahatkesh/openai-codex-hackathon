"""Capability metadata endpoints for UFC build-time discovery."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.models import ToolDefinition
from app.services.capabilities_service import get_tool_definition
from app.services.manifest_service import build_runtime_manifest

router = APIRouter(prefix="/api/capabilities", tags=["capabilities"])


def _serialize_capability(tool: ToolDefinition) -> dict:
    manifest = build_runtime_manifest(tool)
    return {
        "id": str(tool.id),
        "name": tool.name,
        "description": tool.description,
        "provider": tool.provider,
        "status": tool.status,
        "category": tool.category,
        "source": tool.source,
        "version": tool.version,
        "billing": manifest["billing"],
        "runtime_endpoint": manifest["runtime_endpoint"],
        "manifest_endpoint": manifest["manifest_endpoint"],
        "created_at": tool.created_at.isoformat() if tool.created_at else None,
        "updated_at": tool.updated_at.isoformat() if tool.updated_at else None,
    }


@router.get("")
async def list_capabilities(
    status: str | None = None,
    category: str | None = None,
    session: AsyncSession = Depends(get_session),
):
    """List live or filtered FuseKit capabilities with runtime contracts."""
    query = select(ToolDefinition)
    if status:
        query = query.where(ToolDefinition.status == status)
    if category:
        query = query.where(ToolDefinition.category == category)

    query = query.order_by(ToolDefinition.created_at.desc())
    result = await session.execute(query)
    tools = result.scalars().all()
    return [_serialize_capability(tool) for tool in tools]


@router.get("/{tool_name}/manifest")
async def get_capability_manifest_http(tool_name: str):
    """Return the canonical runtime contract for a FuseKit capability."""
    tool = await get_tool_definition(tool_name)
    if tool is None:
        raise HTTPException(
            status_code=404,
            detail={
                "error_code": "TOOL_NOT_FOUND",
                "message": f"TOOL_NOT_FOUND: '{tool_name}' is not in the live catalog.",
            },
        )

    return build_runtime_manifest(tool)
