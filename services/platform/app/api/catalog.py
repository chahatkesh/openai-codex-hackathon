"""Catalog API routes — /api/catalog."""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.models import ToolDefinition

router = APIRouter(prefix="/api/catalog", tags=["catalog"])


@router.get("")
async def list_catalog(
    status: str | None = None,
    category: str | None = None,
    session: AsyncSession = Depends(get_session),
):
    """List all tools in the catalog."""
    query = select(ToolDefinition)
    if status:
        query = query.where(ToolDefinition.status == status)
    if category:
        query = query.where(ToolDefinition.category == category)

    query = query.order_by(ToolDefinition.created_at.desc())
    result = await session.execute(query)
    tools = result.scalars().all()

    return [
        {
            "id": str(t.id),
            "name": t.name,
            "description": t.description,
            "provider": t.provider,
            "cost_per_call": t.cost_per_call,
            "status": t.status,
            "category": t.category,
            "input_schema": t.input_schema,
            "source": t.source,
            "version": t.version,
            "created_at": t.created_at.isoformat() if t.created_at else None,
        }
        for t in tools
    ]


@router.get("/stats")
async def catalog_stats(session: AsyncSession = Depends(get_session)):
    """Get catalog statistics."""
    result = await session.execute(select(ToolDefinition))
    tools = result.scalars().all()

    total = len(tools)
    live = sum(1 for t in tools if t.status == "live")
    pending = sum(1 for t in tools if t.status == "pending_credentials")

    categories = {}
    for t in tools:
        categories[t.category] = categories.get(t.category, 0) + 1

    return {
        "total": total,
        "live": live,
        "pending_credentials": pending,
        "by_category": categories,
    }


@router.get("/recent")
async def recent_catalog(
    limit: int = 20,
    session: AsyncSession = Depends(get_session),
):
    """Return tools created within the last 24 hours."""
    effective_limit = max(1, min(limit, 100))
    since = datetime.now(timezone.utc) - timedelta(hours=24)

    result = await session.execute(
        select(ToolDefinition)
        .where(ToolDefinition.created_at >= since)
        .order_by(ToolDefinition.created_at.desc())
        .limit(effective_limit)
    )
    tools = result.scalars().all()

    return [
        {
            "id": str(t.id),
            "name": t.name,
            "description": t.description,
            "provider": t.provider,
            "cost_per_call": t.cost_per_call,
            "status": t.status,
            "category": t.category,
            "input_schema": t.input_schema,
            "source": t.source,
            "version": t.version,
            "created_at": t.created_at.isoformat() if t.created_at else None,
        }
        for t in tools
    ]
