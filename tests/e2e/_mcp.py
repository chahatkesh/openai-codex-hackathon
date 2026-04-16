from __future__ import annotations

from typing import Any


class McpTestClient:
    def __init__(self, http_url: str):
        self.http_url = http_url
        self._streams = None
        self._session = None

    async def __aenter__(self) -> "McpTestClient":
        from mcp import ClientSession
        from mcp.client.streamable_http import streamable_http_client

        self._streams = streamable_http_client(self.http_url)
        read_stream, write_stream, _get_session_id = await self._streams.__aenter__()
        self._session = ClientSession(read_stream, write_stream)
        await self._session.__aenter__()
        await self._session.initialize()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        if self._session is not None:
            await self._session.__aexit__(exc_type, exc, tb)
        if self._streams is not None:
            await self._streams.__aexit__(exc_type, exc, tb)

    async def list_tools(self) -> list[Any]:
        tools = await self._session.list_tools()
        if hasattr(tools, "tools"):
            return list(tools.tools)
        return list(tools)

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> str:
        result = await self._session.call_tool(name, arguments)
        content = getattr(result, "content", result)
        if isinstance(content, list):
            return "\n".join(getattr(item, "text", "") for item in content if getattr(item, "text", ""))
        return str(content)
