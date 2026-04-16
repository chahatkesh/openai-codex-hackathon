from __future__ import annotations

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
async def test_insufficient_funds_blocks_tool_calls(service_config, api_client):
    # Get scrape_url tool cost from catalog.
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
            max(cost - 1, 0),
        )

        async with McpTestClient(service_config.mcp_http_url) as mcp:
            text = await mcp.call_tool("scrape_url", {"url": f"{service_config.api_base_url}/health"})
            assert "INSUFFICIENT_FUNDS" in text
    finally:
        await conn.execute(
            "update users set wallet_balance = $1 where mcp_auth_token = 'demo-token-fusekit-2026'",
            original_balance,
        )
        await conn.close()


@pytest.mark.asyncio
async def test_refund_on_execution_error(service_config, api_client):
    before_resp = await api_client.get(f"{service_config.api_base_url}/api/wallet/balance")
    before_resp.raise_for_status()
    before_balance = before_resp.json()["balance"]

    async with McpTestClient(service_config.mcp_http_url) as mcp:
        text = await mcp.call_tool("scrape_url", {"url": "http://127.0.0.1:9/nope"})
        assert "EXECUTION_ERROR" in text

    after_resp = await api_client.get(f"{service_config.api_base_url}/api/wallet/balance")
    after_resp.raise_for_status()
    after_balance = after_resp.json()["balance"]
    assert after_balance == before_balance
