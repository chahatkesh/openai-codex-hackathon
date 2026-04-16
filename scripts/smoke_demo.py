#!/usr/bin/env python3
"""End-to-end smoke test for FuseKit demo critical path.

Usage:
  python scripts/smoke_demo.py
  SMOKE_MODE=live python scripts/smoke_demo.py
"""

from __future__ import annotations

import asyncio
import os
import re
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

import httpx

try:
    import asyncpg
except ModuleNotFoundError:
    asyncpg = None


API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
MCP_HTTP_URL = os.getenv("MCP_HTTP_URL", f"{API_BASE_URL}/mcp/http")
SMOKE_MODE = os.getenv("SMOKE_MODE", "stub").strip().lower()
SMOKE_DOCS_URL = os.getenv("SMOKE_DOCS_URL", "https://example.com/docs")
SMOKE_TOOL_NAME = os.getenv("SMOKE_TOOL_NAME", "demo_generated_tool")
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://fusekit:fusekit@localhost:5432/fusekit",
)
POLL_INTERVAL_SECONDS = float(os.getenv("SMOKE_POLL_INTERVAL_SECONDS", "2.0"))
POLL_TIMEOUT_SECONDS = int(os.getenv("SMOKE_POLL_TIMEOUT_SECONDS", "180"))


@dataclass
class StepResult:
    index: int
    label: str
    ok: bool
    detail: str


def _print_result(result: StepResult) -> None:
    status = "PASS" if result.ok else "FAIL"
    print(f"[{status}] Step {result.index}: {result.label} - {result.detail}")


class SmokeFailure(RuntimeError):
    pass


class McpClient:
    """Small wrapper around MCP streamable HTTP client APIs."""

    def __init__(self, http_url: str):
        self.http_url = http_url
        self._streams = None
        self._session = None

    async def __aenter__(self) -> "McpClient":
        try:
            from mcp import ClientSession
            from mcp.client.streamable_http import streamable_http_client
        except ModuleNotFoundError as exc:
            raise SmokeFailure(
                "mcp package is not installed. Install platform dependencies first."
            ) from exc

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
        result = await self._session.list_tools()
        if hasattr(result, "tools"):
            return list(result.tools)
        return list(result)

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> str:
        result = await self._session.call_tool(name, arguments)
        content = getattr(result, "content", result)
        if isinstance(content, list):
            texts: list[str] = []
            for item in content:
                item_text = getattr(item, "text", "")
                if item_text:
                    texts.append(item_text)
            return "\n".join(texts).strip()
        return str(content)


def _clean_db_url(url: str) -> str:
    return url.replace("+asyncpg", "")


async def _fetch_latest_integration_job_id(after_ts: datetime) -> str | None:
    if asyncpg is None:
        return None

    conn = await asyncpg.connect(_clean_db_url(DATABASE_URL))
    try:
        row = await conn.fetchrow(
            """
            SELECT id::text
            FROM integration_jobs
            WHERE created_at >= $1
            ORDER BY created_at DESC
            LIMIT 1
            """,
            after_ts,
        )
        if not row:
            return None
        return str(row["id"])
    finally:
        await conn.close()


def _looks_like_uuid(value: str) -> bool:
    try:
        UUID(value)
        return True
    except ValueError:
        return False


def _extract_uuid(text: str) -> str | None:
    match = re.search(
        r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}\b",
        text,
    )
    if not match:
        return None
    return match.group(0)


def _build_args_from_schema(schema: dict[str, Any] | None) -> dict[str, Any]:
    """Build a minimal deterministic payload from a JSON schema."""
    if not schema:
        return {}

    properties = schema.get("properties", {})
    required = schema.get("required", [])
    args: dict[str, Any] = {}

    for key in required:
        prop = properties.get(key, {})
        if "default" in prop:
            args[key] = prop["default"]
            continue

        prop_type = prop.get("type")
        if prop_type == "string":
            if "url" in key:
                args[key] = "https://example.com"
            elif "email" in key or key == "to":
                args[key] = "demo@example.com"
            elif "phone" in key:
                args[key] = "+10000000000"
            else:
                args[key] = "smoke-test"
        elif prop_type == "integer":
            args[key] = 1
        elif prop_type == "number":
            args[key] = 1
        elif prop_type == "boolean":
            args[key] = False
        elif prop_type == "array":
            args[key] = []
        elif prop_type == "object":
            args[key] = {}
        else:
            args[key] = "smoke-test"

    return args


async def run() -> int:
    if SMOKE_MODE not in {"stub", "live"}:
        print("SMOKE_MODE must be one of: stub, live")
        return 2

    results: list[StepResult] = []
    missing_job_id: str | None = None
    manual_job_id: str | None = None
    new_tool_name: str | None = None

    async with httpx.AsyncClient(timeout=30) as client:
        try:
            # Step 1
            resp = await client.get(f"{API_BASE_URL}/health")
            data = resp.json()
            ok = resp.status_code == 200 and data.get("status") == "ok"
            result = StepResult(1, "GET /health", ok, f"status={resp.status_code}, body={data}")
            results.append(result)
            _print_result(result)
            if not ok:
                raise SmokeFailure("Health check failed")

            async with McpClient(MCP_HTTP_URL) as mcp:
                # Step 2
                tools = await mcp.list_tools()
                tool_names = {getattr(t, "name", None) for t in tools}
                expected = {
                    "scrape_url",
                    "send_email",
                    "search_web",
                    "get_producthunt",
                    "request_integration",
                }
                ok = expected.issubset(tool_names)
                result = StepResult(
                    2,
                    "MCP tools/list",
                    ok,
                    f"found={len(tool_names)} tools",
                )
                results.append(result)
                _print_result(result)
                if not ok:
                    raise SmokeFailure("tools/list missing required tools")

                # Step 3
                scrape_target = f"{API_BASE_URL}/health" if SMOKE_MODE == "stub" else "https://example.com"
                scrape_text = await mcp.call_tool("scrape_url", {"url": scrape_target})
                ok = bool(scrape_text) and "EXECUTION_ERROR" not in scrape_text
                result = StepResult(
                    3,
                    "MCP tools/call scrape_url",
                    ok,
                    f"response_preview={scrape_text[:80]!r}",
                )
                results.append(result)
                _print_result(result)
                if not ok:
                    raise SmokeFailure("scrape_url tool call failed")

                # Step 4
                before_balance_resp = await client.get(f"{API_BASE_URL}/api/wallet/balance")
                before_balance_data = before_balance_resp.json()
                before_balance = before_balance_data.get("balance")
                await mcp.call_tool("scrape_url", {"url": scrape_target})
                after_balance_resp = await client.get(f"{API_BASE_URL}/api/wallet/balance")
                after_balance_data = after_balance_resp.json()
                after_balance = after_balance_data.get("balance")
                ok = isinstance(before_balance, int) and isinstance(after_balance, int) and after_balance < before_balance
                result = StepResult(
                    4,
                    "Wallet deduction after tool call",
                    ok,
                    f"before={before_balance}, after={after_balance}",
                )
                results.append(result)
                _print_result(result)
                if not ok:
                    raise SmokeFailure("wallet balance did not decrease")

                # Step 5
                step5_started_at = datetime.now(tz=timezone.utc)
                missing_tool_response = await mcp.call_tool(
                    "__missing_tool_for_smoke__", {"value": "demo"}
                )
                ok = "TOOL_NOT_FOUND" in missing_tool_response
                missing_job_id = _extract_uuid(missing_tool_response)
                result = StepResult(
                    5,
                    "MCP tools/call missing tool",
                    ok,
                    f"response_preview={missing_tool_response[:120]!r}",
                )
                results.append(result)
                _print_result(result)
                if not ok:
                    raise SmokeFailure("missing tool did not return TOOL_NOT_FOUND")

            # Step 6
            if not missing_job_id:
                missing_job_id = await _fetch_latest_integration_job_id(step5_started_at)
            if not missing_job_id:
                result = StepResult(
                    6,
                    "GET /api/integrate/{job_id} (auto-created)",
                    False,
                    "could not resolve auto-created integration job id",
                )
                results.append(result)
                _print_result(result)
                raise SmokeFailure("could not resolve auto-created job id")

            step6_resp = await client.get(f"{API_BASE_URL}/api/integrate/{missing_job_id}")
            ok = step6_resp.status_code == 200
            step6_body = step6_resp.json() if step6_resp.status_code == 200 else step6_resp.text
            result = StepResult(
                6,
                "GET /api/integrate/{job_id} (auto-created)",
                ok,
                f"job_id={missing_job_id}, status={step6_resp.status_code}",
            )
            results.append(result)
            _print_result(result)
            if not ok:
                raise SmokeFailure(f"failed to fetch auto-created job: {step6_body}")

            # Step 7
            payload = {
                "docs_url": SMOKE_DOCS_URL,
                "requested_by": "user",
                "requested_tool_name": SMOKE_TOOL_NAME,
            }
            step7_resp = await client.post(f"{API_BASE_URL}/api/integrate", json=payload)
            step7_body = step7_resp.json() if step7_resp.status_code < 500 else {"raw": step7_resp.text}
            manual_job_id = step7_body.get("job_id")
            ok = step7_resp.status_code in {200, 201, 202} and bool(manual_job_id)
            result = StepResult(
                7,
                "POST /api/integrate",
                ok,
                f"status={step7_resp.status_code}, job_id={manual_job_id}",
            )
            results.append(result)
            _print_result(result)
            if not ok:
                raise SmokeFailure(f"failed to create integration job: {step7_body}")

            # Step 8
            started = time.monotonic()
            terminal_statuses = {"complete", "failed"}
            final_status = None
            while time.monotonic() - started <= POLL_TIMEOUT_SECONDS:
                poll_resp = await client.get(f"{API_BASE_URL}/api/integrate/{manual_job_id}")
                if poll_resp.status_code != 200:
                    await asyncio.sleep(POLL_INTERVAL_SECONDS)
                    continue
                poll_data = poll_resp.json()
                final_status = poll_data.get("status")
                if final_status in terminal_statuses:
                    break
                await asyncio.sleep(POLL_INTERVAL_SECONDS)

            ok = final_status == "complete"
            result = StepResult(
                8,
                "Poll integration status to completion",
                ok,
                f"final_status={final_status}",
            )
            results.append(result)
            _print_result(result)
            if not ok:
                raise SmokeFailure("integration job did not complete")

            # Step 9
            async with McpClient(MCP_HTTP_URL) as mcp:
                tools = await mcp.list_tools()
                tool_names = {getattr(t, "name", None) for t in tools}
                if SMOKE_TOOL_NAME in tool_names:
                    new_tool_name = SMOKE_TOOL_NAME
                elif manual_job_id and _looks_like_uuid(manual_job_id):
                    # Keep fallback behavior predictable when generated name differs.
                    new_tool_name = next(
                        (name for name in tool_names if name not in {
                            "scrape_url", "send_email", "search_web", "get_producthunt"
                        }),
                        None,
                    )
                ok = bool(new_tool_name)
                result = StepResult(
                    9,
                    "MCP tools/list includes new tool",
                    ok,
                    f"new_tool={new_tool_name}",
                )
                results.append(result)
                _print_result(result)
                if not ok:
                    raise SmokeFailure("new tool did not appear in tools/list")

                # Step 10
                catalog_resp = await client.get(f"{API_BASE_URL}/api/catalog")
                catalog_resp.raise_for_status()
                catalog_items = catalog_resp.json()
                tool_item = next((t for t in catalog_items if t.get("name") == new_tool_name), None)
                call_args = _build_args_from_schema(tool_item.get("input_schema") if tool_item else None)
                response_text = await mcp.call_tool(new_tool_name, call_args)
                ok = bool(response_text) and "EXECUTION_ERROR" not in response_text
                result = StepResult(
                    10,
                    "MCP tools/call new tool",
                    ok,
                    f"args={call_args}, response_preview={response_text[:120]!r}",
                )
                results.append(result)
                _print_result(result)
                if not ok:
                    raise SmokeFailure("new tool call failed")

        except SmokeFailure as exc:
            print(f"\nSmoke test failed: {exc}")
            return 1
        except Exception as exc:  # pragma: no cover
            print(f"\nUnexpected smoke test error: {exc}")
            return 1

    passed = sum(1 for r in results if r.ok)
    print(f"\nSmoke test completed: {passed}/{len(results)} steps passed.")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run()))
