from __future__ import annotations

import uuid

import pytest

from app.api.execute import execute_tool_http
from app.services.capabilities_service import ExecutionResult


@pytest.mark.asyncio
async def test_execute_tool_http_returns_success_payload(monkeypatch):
    async def fake_get_tool_definition(_tool_name: str):
        return object()

    async def fake_get_user_id_for_token(_token: str):
        return uuid.uuid4()

    async def fake_execute_capability(**_kwargs):
        return ExecutionResult(
            ok=True,
            tool_name="scrape_url",
            text="page text",
            balance_after=90,
        )

    monkeypatch.setattr("app.api.execute.get_tool_definition", fake_get_tool_definition)
    monkeypatch.setattr("app.api.execute.get_user_id_for_token", fake_get_user_id_for_token)
    monkeypatch.setattr("app.api.execute.execute_capability", fake_execute_capability)

    payload = await execute_tool_http(
        "scrape_url",
        payload={"url": "https://example.com"},
        authorization=None,
    )

    assert payload["tool_name"] == "scrape_url"
    assert payload["data"] is None
    assert payload["data_format"] == "text"
    assert payload["raw_result"] == "page text"
    assert payload["result"] == "page text"
    assert payload["balance_after"] == 90


@pytest.mark.asyncio
async def test_execute_tool_http_decodes_json_result(monkeypatch):
    async def fake_get_tool_definition(_tool_name: str):
        return object()

    async def fake_get_user_id_for_token(_token: str):
        return uuid.uuid4()

    async def fake_execute_capability(**_kwargs):
        return ExecutionResult(
            ok=True,
            tool_name="get_producthunt",
            text='[{"name":"Demo","votes":10}]',
            balance_after=90,
        )

    monkeypatch.setattr("app.api.execute.get_tool_definition", fake_get_tool_definition)
    monkeypatch.setattr("app.api.execute.get_user_id_for_token", fake_get_user_id_for_token)
    monkeypatch.setattr("app.api.execute.execute_capability", fake_execute_capability)

    payload = await execute_tool_http(
        "get_producthunt",
        payload={"category": "tech"},
        authorization=None,
    )

    assert payload["data_format"] == "json"
    assert payload["data"] == [{"name": "Demo", "votes": 10}]
    assert payload["raw_result"] == '[{"name":"Demo","votes":10}]'
