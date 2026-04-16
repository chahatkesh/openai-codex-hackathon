from __future__ import annotations

import pytest

from app.agents.reader import run_reader
from app.docs_fetcher import DocsBundle, DocsPage
from app.schemas import DiscoveryResult


class FakeLLM:
    async def generate_json(self, _system_prompt: str, _user_prompt: str):
        return {
            "provider_name": "Example API",
            "base_url": "https://api.example.com",
            "auth": {"method": "bearer"},
            "endpoints": [
                {
                    "path": "/v1/items",
                    "method": "GET",
                    "required_params": [],
                    "optional_params": ["limit"],
                    "request_body": {},
                    "response": {"type": "array"},
                }
            ],
            "errors": [{"code": "401", "description": "Unauthorized"}],
        }


@pytest.mark.asyncio
async def test_reader_extracts_spec(monkeypatch):
    async def fake_fetch_bundle(_url: str, max_pages: int = 3):  # noqa: ARG001
        return DocsBundle(
            provider="jina",
            pages=[
                DocsPage(
                    url="https://example.com/docs",
                    title="Example API",
                    markdown="API docs",
                )
            ],
        )

    monkeypatch.setattr("app.agents.reader.fetch_docs_bundle_result", fake_fetch_bundle)

    discovery = DiscoveryResult(provider_name="Example API", auth_method="bearer")
    spec = await run_reader("https://example.com/docs", discovery, FakeLLM())

    assert spec.provider_name == "Example API"
    assert spec.endpoints[0]["path"] == "/v1/items"
    assert spec.errors[0]["code"] == "401"
