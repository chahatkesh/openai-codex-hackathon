from __future__ import annotations

import pytest

from app.docs_fetcher import _parse_html_page, _parse_openapi_document, fetch_docs_bundle


def test_parse_html_page_extracts_structure():
    page = _parse_html_page(
        "https://docs.example.com/auth",
        """
        <html>
          <head><title>Authentication</title></head>
          <body>
            <main>
              <h1>Authentication</h1>
              <p>Use Bearer tokens in the Authorization header.</p>
              <pre>curl -H "Authorization: Bearer token"</pre>
              <a href="/reference">API Reference</a>
            </main>
          </body>
        </html>
        """,
    )

    assert page.title == "Authentication"
    assert "Authentication" in page.headings
    assert any("Bearer" in hint for hint in page.auth_hints)
    assert any("Authorization: Bearer token" in block for block in page.code_blocks)
    assert page.links == ["https://docs.example.com/reference"]


def test_parse_openapi_document_extracts_endpoints():
    page = _parse_openapi_document(
        "https://docs.example.com/openapi.json",
        """
        {
          "openapi": "3.1.0",
          "info": { "title": "Example API" },
          "servers": [{ "url": "https://api.example.com" }],
          "paths": {
            "/users": { "get": {}, "post": {} }
          },
          "components": {
            "securitySchemes": {
              "bearerAuth": { "type": "http", "scheme": "bearer" }
            }
          }
        }
        """,
    )

    assert page.title == "Example API"
    assert page.metadata["base_url"] == "https://api.example.com"
    assert "GET /users" in page.endpoint_hints
    assert any("bearerAuth" in hint for hint in page.auth_hints)


@pytest.mark.asyncio
async def test_fetch_docs_bundle_formats_multiple_pages(monkeypatch):
    async def fake_fetch_document(url: str):
        if url.endswith("/docs"):
            return _parse_html_page(
                url,
                """
                <html><body><main>
                <h1>Example Docs</h1>
                <a href="/auth">Authentication</a>
                </main></body></html>
                """,
            )
        return _parse_html_page(
            url,
            """
            <html><body><main>
            <h1>Authentication</h1>
            <p>Use API key auth.</p>
            </main></body></html>
            """,
        )

    monkeypatch.setattr("app.docs_fetcher.fetch_document", fake_fetch_document)

    bundle = await fetch_docs_bundle("https://docs.example.com/docs", max_pages=2)

    assert "Source URL: https://docs.example.com/docs" in bundle
    assert "Source URL: https://docs.example.com/auth" in bundle
    assert "Auth hints:" in bundle
