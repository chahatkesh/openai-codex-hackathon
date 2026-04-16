from __future__ import annotations

import pytest

from app.agents.discovery import run_discovery


class FakeLLM:
    async def generate_json(self, _system_prompt: str, _user_prompt: str):
        return {
            "provider_name": "Example API",
            "base_url": "https://api.example.com",
            "auth_method": "bearer",
            "key_endpoints": ["/v1/items"],
            "rate_limits": "100/min",
            "sandbox_available": True,
        }


@pytest.mark.asyncio
async def test_discovery_returns_structured_result(monkeypatch):
    async def fake_fetch_docs_bundle(_url: str, max_pages: int = 2) -> str:  # noqa: ARG001
        return "Title: Example API\n\nAuth hints:\n- Bearer token"

    monkeypatch.setattr("app.agents.discovery.fetch_docs_bundle", fake_fetch_docs_bundle)

    result = await run_discovery("https://example.com/docs", FakeLLM())

    assert result.provider_name == "Example API"
    assert result.auth_method == "bearer"
    assert result.key_endpoints == ["/v1/items"]
