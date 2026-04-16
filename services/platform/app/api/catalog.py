"""Legacy catalog API routes — /api/catalog."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.capabilities import capability_stats, list_capabilities, recent_capabilities
from app.db import get_session

router = APIRouter(prefix="/api/catalog", tags=["catalog"])


@router.get("")
async def list_catalog(
    status: str | None = None,
    category: str | None = None,
    session: AsyncSession = Depends(get_session),
):
    """List all tools in the catalog.

    Legacy alias for the capability-first catalog surface.
    """
    return await list_capabilities(status=status, category=category, session=session)


@router.get("/stats")
async def catalog_stats(session: AsyncSession = Depends(get_session)):
    """Legacy alias for capability statistics."""
    return await capability_stats(session=session)


@router.get("/recent")
async def recent_catalog(
    limit: int = 20,
    session: AsyncSession = Depends(get_session),
):
    """Legacy alias for recent capabilities."""
    return await recent_capabilities(limit=limit, session=session)
