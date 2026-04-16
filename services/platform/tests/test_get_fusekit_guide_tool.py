from __future__ import annotations

import pytest

from app.tools import get_fusekit_guide


@pytest.mark.asyncio
async def test_get_fusekit_guide_returns_build_and_runtime_guidance():
    payload = await get_fusekit_guide.execute()

    assert "Use MCP only at build time." in payload
    assert "Use FuseKit HTTP endpoints at runtime." in payload
    assert "get_capability_manifest" in payload
    assert "request_integration" in payload
