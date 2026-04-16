"""Capability metadata endpoints for UFC build-time discovery."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

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
    detail_path = f"/api/capabilities/{tool.name}"
    detail_url = f"{manifest['base_url']}{detail_path}"
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
        "detail_endpoint": {
            "method": "GET",
            "path": detail_path,
            "url": detail_url,
        },
        "artifacts": manifest["artifacts"],
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


@router.get("/stats")
async def capability_stats(session: AsyncSession = Depends(get_session)):
    """Get capability catalog statistics."""
    result = await session.execute(select(ToolDefinition))
    tools = result.scalars().all()

    total = len(tools)
    live = sum(1 for t in tools if t.status == "live")
    pending = sum(1 for t in tools if t.status == "pending_credentials")

    categories: dict[str, int] = {}
    for tool in tools:
        categories[tool.category] = categories.get(tool.category, 0) + 1

    return {
        "total": total,
        "live": live,
        "pending_credentials": pending,
        "by_category": categories,
    }


@router.get("/recent")
async def recent_capabilities(
    limit: int = 20,
    session: AsyncSession = Depends(get_session),
):
    """Return recently published capabilities with runtime metadata."""
    effective_limit = max(1, min(limit, 100))
    since = datetime.now(timezone.utc) - timedelta(hours=24)

    result = await session.execute(
        select(ToolDefinition)
        .where(ToolDefinition.created_at >= since)
        .order_by(ToolDefinition.created_at.desc())
        .limit(effective_limit)
    )
    tools = result.scalars().all()
    return [_serialize_capability(tool) for tool in tools]


@router.get("/{tool_name}")
async def get_capability_detail(tool_name: str):
    """Return capability metadata plus the canonical manifest."""
    tool = await get_tool_definition(tool_name)
    if tool is None:
        raise HTTPException(
            status_code=404,
            detail={
                "error_code": "TOOL_NOT_FOUND",
                "message": f"TOOL_NOT_FOUND: '{tool_name}' is not in the live catalog.",
            },
        )

    payload = _serialize_capability(tool)
    payload["manifest"] = build_runtime_manifest(tool)
    return payload


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
