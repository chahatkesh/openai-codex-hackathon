"""Capability metadata endpoints for UFC build-time discovery."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.services.capabilities_service import get_tool_definition
from app.services.manifest_service import build_runtime_manifest

router = APIRouter(prefix="/api/capabilities", tags=["capabilities"])


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
