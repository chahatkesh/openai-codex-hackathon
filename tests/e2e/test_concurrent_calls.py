from __future__ import annotations

import asyncio
import os

import pytest

from ._mcp import McpTestClient


pytest.importorskip("mcp")
asyncpg = pytest.importorskip("asyncpg")


def _db_url() -> str:
    return os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://fusekit:fusekit@localhost:5432/fusekit",
    ).replace("+asyncpg", "")


@pytest.mark.asyncio
async def test_wallet_deductions_are_atomic_under_concurrency(service_config, api_client):
    catalog_resp = await api_client.get(f"{service_config.api_base_url}/api/catalog")
    catalog_resp.raise_for_status()
    scrape_item = next(item for item in catalog_resp.json() if item["name"] == "scrape_url")
    cost = scrape_item["cost_per_call"]

    conn = await asyncpg.connect(_db_url())
    original_balance = 10000
    try:
        original_balance = await conn.fetchval(
            "select wallet_balance from users where mcp_auth_token = 'demo-token-fusekit-2026'"
        )
        await conn.execute(
            "update users set wallet_balance = $1 where mcp_auth_token = 'demo-token-fusekit-2026'",
            cost * 5,
        )

        async def worker() -> str:
            async with McpTestClient(service_config.mcp_http_url) as mcp:
                return await mcp.call_tool("scrape_url", {"url": f"{service_config.api_base_url}/health"})

        results = await asyncio.gather(*(worker() for _ in range(10)))
        success_count = sum(1 for r in results if "INSUFFICIENT_FUNDS" not in r and "EXECUTION_ERROR" not in r)
        insufficient_count = sum(1 for r in results if "INSUFFICIENT_FUNDS" in r)

        final_balance = await conn.fetchval(
            "select wallet_balance from users where mcp_auth_token = 'demo-token-fusekit-2026'"
        )
    finally:
        await conn.execute(
            "update users set wallet_balance = $1 where mcp_auth_token = 'demo-token-fusekit-2026'",
            original_balance,
        )
        await conn.close()

    assert success_count <= 5
    assert insufficient_count >= 1
    assert final_balance >= 0
