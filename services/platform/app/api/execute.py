"""Generic HTTP execution endpoint for deployed apps."""

from __future__ import annotations

import json

from fastapi import APIRouter, Body, Header, HTTPException

from app.services.capabilities_service import (
    DEMO_USER_TOKEN,
    execute_capability,
    get_tool_definition,
    get_user_id_for_token,
)

router = APIRouter(prefix="/api/execute", tags=["execute"])


def _parse_bearer_token(authorization: str | None) -> str:
    if not authorization:
        return DEMO_USER_TOKEN
    prefix = "Bearer "
    if authorization.startswith(prefix):
        return authorization[len(prefix):].strip() or DEMO_USER_TOKEN
    return authorization.strip() or DEMO_USER_TOKEN


def _decode_result_payload(text: str) -> tuple[str, object | None]:
    try:
        return "json", json.loads(text)
    except Exception:
        return "text", None


@router.post("/{tool_name}")
async def execute_tool_http(
    tool_name: str,
    payload: dict = Body(default_factory=dict),
    authorization: str | None = Header(default=None),
):
    """Execute a FuseKit capability over HTTP for deployed apps."""
    tool_def = await get_tool_definition(tool_name)
    if tool_def is None:
        raise HTTPException(
            status_code=404,
            detail={
                "error_code": "TOOL_NOT_FOUND",
                "message": (
                    f"TOOL_NOT_FOUND: '{tool_name}' is not in the catalog. "
                    "Request integration through the FuseKit MCP interface."
                ),
            },
        )

    user_id = await get_user_id_for_token(_parse_bearer_token(authorization))
    result = await execute_capability(
        user_id=user_id,
        tool_name=tool_name,
        arguments=payload,
    )

    if result.is_error:
        status_code = 402 if result.error_code == "INSUFFICIENT_FUNDS" else 500
        raise HTTPException(
            status_code=status_code,
            detail={
                "error_code": result.error_code,
                "message": result.text,
            },
        )

    result_format, decoded = _decode_result_payload(result.text)
    return {
        "tool_name": result.tool_name,
        "data": decoded,
        "data_format": result_format,
        "raw_result": result.text,
        "result": result.text,
        "balance_after": result.balance_after,
    }
