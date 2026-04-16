from __future__ import annotations

import json

import pytest

from app.tools import scrape_url


class _Response:
    def __init__(self, url: str, text: str, content_type: str = "text/html"):
        self.url = url
        self.status_code = 200
        self.encoding = "utf-8"
        self._text = text
        self.content = text.encode("utf-8")
        self.headers = {"content-type": content_type}

    @property
    def text(self) -> str:
        return self._text

    def raise_for_status(self) -> None:
        return None


class _Client:
    def __init__(self, response: _Response):
        self.response = response

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def get(self, _url: str, headers: dict[str, str]):
        assert "User-Agent" in headers
        return self.response


@pytest.mark.asyncio
async def test_scrape_url_returns_structured_json(monkeypatch):
    response = _Response(
        "https://docs.example.com/auth",
        """
        <html><head><title>Authentication</title></head>
        <body><main>
          <h1>Authentication</h1>
          <p>Use Bearer tokens in the Authorization header.</p>
          <pre>curl -H "Authorization: Bearer token"</pre>
        </main></body></html>
        """,
    )

    monkeypatch.setattr("app.tools.scrape_url.httpx.AsyncClient", lambda **kwargs: _Client(response))

    raw = await scrape_url.execute("https://docs.example.com/auth")
    payload = json.loads(raw)

    assert payload["title"] == "Authentication"
    assert payload["content_type"] == "text/html"
    assert "Authorization header" in payload["text"]
    assert payload["metadata"]["status_code"] == 200
