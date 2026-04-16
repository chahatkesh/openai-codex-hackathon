"""Quick end-to-end test: connect to MCP server and call scrape_url (15 credits).

Usage:
    cd services/platform
    PYTHONPATH=. python ../../scripts/quick_test.py
"""

import asyncio
import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client


MCP_URL = "http://localhost:8000/mcp/http"
WALLET_URL = "http://localhost:8000/api/wallet/balance"


async def main():
    # 1. Check wallet before
    async with httpx.AsyncClient() as http:
        before = (await http.get(WALLET_URL)).json()
    print(f"1. Wallet BEFORE: {before['balance']} credits")

    # 2. Connect to MCP and list tools
    async with streamable_http_client(MCP_URL) as streams:
        async with ClientSession(*streams[:2]) as session:
            await session.initialize()

            tools = await session.list_tools()
            print(f"2. Tools available: {[t.name for t in tools.tools]}")

            # 3. Call scrape_url on a tiny page (15 credits)
            print("3. Calling scrape_url on example.com...")
            result = await session.call_tool(
                "scrape_url", {"url": "https://example.com"}
            )
            text = result.content[0].text
            print(f"   Result ({len(text)} chars): {text[:200]}...")

    # 4. Check wallet after
    async with httpx.AsyncClient() as http:
        after = (await http.get(WALLET_URL)).json()
    print(f"4. Wallet AFTER:  {after['balance']} credits (spent {before['balance'] - after['balance']})")

    print("\n✅ End-to-end test passed!")


if __name__ == "__main__":
    asyncio.run(main())
