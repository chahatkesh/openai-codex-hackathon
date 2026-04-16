from __future__ import annotations

import pytest

from app.docs_fetcher import DocsBundle, DocsPage, _build_jina_reader_url, fetch_docs_bundle_result


def test_docs_bundle_combines_pages():
    bundle = DocsBundle(
        provider="basic",
        pages=[
            DocsPage(url="https://example.com/docs", title="Docs Home", markdown="Hello"),
            DocsPage(url="https://example.com/auth", title="Auth", markdown="Bearer token"),
        ],
    )

    combined = bundle.combined_markdown()

    assert "Docs Home" in combined
    assert "https://example.com/auth" in combined
    assert "Bearer token" in combined


def test_build_jina_reader_url(settings_override):
    settings_override.jina_reader_base_url = "https://r.jina.ai"
    assert _build_jina_reader_url("https://example.com/docs") == "https://r.jina.ai/https://example.com/docs"


@pytest.mark.asyncio
async def test_fetch_docs_bundle_auto_falls_back_to_basic(monkeypatch, settings_override):
    settings_override.docs_fetch_provider = "auto"
    settings_override.firecrawl_api_key = ""

    async def fake_jina(_url: str):
        raise RuntimeError("reader blocked")

    async def fake_basic(_url: str, _max_pages: int):
        return DocsBundle(
            provider="basic",
            pages=[DocsPage(url="https://example.com/docs", markdown="Basic docs")],
        )

    monkeypatch.setattr("app.docs_fetcher._fetch_with_jina", fake_jina)
    monkeypatch.setattr("app.docs_fetcher._fetch_with_basic", fake_basic)

    bundle = await fetch_docs_bundle_result("https://example.com/docs", max_pages=2)

    assert bundle.provider == "basic"
    assert bundle.pages[0].markdown == "Basic docs"
    assert any(error.startswith("firecrawl:") for error in bundle.errors)
    assert any(error.startswith("jina:") for error in bundle.errors)
