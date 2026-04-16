from __future__ import annotations

from dataclasses import dataclass, field
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from app.config import settings

USER_AGENT = "FuseKit-Integrator/1.0"


@dataclass(slots=True)
class DocsPage:
    url: str
    markdown: str
    title: str | None = None
    status_code: int | None = None


@dataclass(slots=True)
class DocsBundle:
    provider: str
    pages: list[DocsPage]
    errors: list[str] = field(default_factory=list)

    def combined_markdown(self, limit: int | None = None) -> str:
        sections: list[str] = []
        for page in self.pages:
            title = page.title or page.url
            sections.append(f"# Source: {title}\nURL: {page.url}\n\n{page.markdown}".strip())

        joined = "\n\n".join(section for section in sections if section.strip())
        if limit is not None and len(joined) > limit:
            return joined[:limit]
        return joined


async def fetch_url(url: str) -> str:
    async with httpx.AsyncClient(
        timeout=settings.docs_fetch_timeout_seconds,
        follow_redirects=True,
    ) as client:
        resp = await client.get(url, headers={"User-Agent": USER_AGENT})
        resp.raise_for_status()
        return resp.text


def html_to_text(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    return soup.get_text(separator="\n", strip=True)


async def fetch_docs_bundle(docs_url: str, max_pages: int | None = None) -> str:
    bundle = await fetch_docs_bundle_result(docs_url, max_pages=max_pages)
    return bundle.combined_markdown()


async def fetch_docs_bundle_result(docs_url: str, max_pages: int | None = None) -> DocsBundle:
    effective_max_pages = max_pages or settings.docs_fetch_max_pages
    provider = settings.docs_fetch_provider.strip().lower()

    if provider == "firecrawl":
        return await _fetch_with_firecrawl(docs_url, effective_max_pages)
    if provider == "jina":
        return await _fetch_with_jina(docs_url)
    if provider == "basic":
        return await _fetch_with_basic(docs_url, effective_max_pages)

    errors: list[str] = []
    for name, fetcher in (
        ("firecrawl", lambda: _fetch_with_firecrawl(docs_url, effective_max_pages)),
        ("jina", lambda: _fetch_with_jina(docs_url)),
        ("basic", lambda: _fetch_with_basic(docs_url, effective_max_pages)),
    ):
        try:
            bundle = await fetcher()
            if bundle.pages:
                bundle.errors = [*errors, *bundle.errors]
                return bundle
            errors.append(f"{name}: no pages returned")
        except Exception as exc:
            errors.append(f"{name}: {exc}")

    return DocsBundle(provider="unavailable", pages=[], errors=errors)


async def _fetch_with_firecrawl(docs_url: str, max_pages: int) -> DocsBundle:
    if not settings.firecrawl_api_key:
        raise RuntimeError("FIRECRAWL_API_KEY missing")

    base_url = settings.firecrawl_api_url.rstrip("/")
    headers = {
        "Authorization": f"Bearer {settings.firecrawl_api_key}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=settings.docs_fetch_timeout_seconds) as client:
        if max_pages <= 1:
            resp = await client.post(
                f"{base_url}/v1/scrape",
                headers=headers,
                json={
                    "url": docs_url,
                    "formats": ["markdown"],
                    "onlyMainContent": True,
                },
            )
            resp.raise_for_status()
            payload = resp.json()
            document = payload.get("data", payload)
            markdown = str(document.get("markdown", "")).strip()
            metadata = document.get("metadata", {}) if isinstance(document, dict) else {}
            return DocsBundle(
                provider="firecrawl",
                pages=[
                    DocsPage(
                        url=str(metadata.get("sourceURL") or metadata.get("url") or docs_url),
                        title=metadata.get("title"),
                        status_code=metadata.get("statusCode"),
                        markdown=markdown,
                    )
                ]
                if markdown
                else [],
            )

        resp = await client.post(
            f"{base_url}/v2/crawl",
            headers=headers,
            json={
                "url": docs_url,
                "limit": min(max_pages, settings.firecrawl_crawl_limit),
                "maxDiscoveryDepth": 1,
                "scrapeOptions": {
                    "formats": ["markdown"],
                    "onlyMainContent": True,
                },
            },
        )
        resp.raise_for_status()
        payload = resp.json()
        data = payload.get("data", [])

    pages: list[DocsPage] = []
    for item in data[:max_pages]:
        if not isinstance(item, dict):
            continue
        markdown = str(item.get("markdown", "")).strip()
        metadata = item.get("metadata", {}) or {}
        if not markdown:
            continue
        pages.append(
            DocsPage(
                url=str(metadata.get("sourceURL") or metadata.get("url") or docs_url),
                title=metadata.get("title"),
                status_code=metadata.get("statusCode"),
                markdown=markdown,
            )
        )

    return DocsBundle(provider="firecrawl", pages=pages)


async def _fetch_with_jina(docs_url: str) -> DocsBundle:
    reader_url = _build_jina_reader_url(docs_url)
    headers = {"User-Agent": USER_AGENT}
    if settings.jina_api_key:
        headers["Authorization"] = f"Bearer {settings.jina_api_key}"

    async with httpx.AsyncClient(
        timeout=settings.docs_fetch_timeout_seconds,
        follow_redirects=True,
    ) as client:
        resp = await client.get(reader_url, headers=headers)
        resp.raise_for_status()
        markdown = resp.text.strip()

    return DocsBundle(
        provider="jina",
        pages=[DocsPage(url=docs_url, markdown=markdown, title="Jina Reader")],
    )


async def _fetch_with_basic(docs_url: str, max_pages: int) -> DocsBundle:
    html = await fetch_url(docs_url)
    soup = BeautifulSoup(html, "lxml")
    base_host = urlparse(docs_url).netloc

    pages = [
        DocsPage(
            url=docs_url,
            markdown=html_to_text(html),
            title=_extract_title(soup),
        )
    ]
    seen = {docs_url}

    for link in soup.select("a[href]"):
        if len(pages) >= max_pages:
            break
        href = link.get("href")
        if not href:
            continue
        absolute = urljoin(docs_url, href)
        parsed = urlparse(absolute)
        if parsed.netloc != base_host:
            continue
        if absolute in seen:
            continue
        seen.add(absolute)
        try:
            sub_html = await fetch_url(absolute)
        except Exception:
            continue
        sub_soup = BeautifulSoup(sub_html, "lxml")
        pages.append(
            DocsPage(
                url=absolute,
                markdown=html_to_text(sub_html),
                title=_extract_title(sub_soup),
            )
        )

    return DocsBundle(provider="basic", pages=pages)


def _build_jina_reader_url(url: str) -> str:
    base = settings.jina_reader_base_url
    if not base.endswith("/"):
        base = f"{base}/"
    return f"{base}{url}"


def _extract_title(soup: BeautifulSoup) -> str | None:
    if soup.title and soup.title.string:
        return soup.title.string.strip()
    heading = soup.find(["h1", "h2"])
    if heading:
        return heading.get_text(" ", strip=True)
    return None
