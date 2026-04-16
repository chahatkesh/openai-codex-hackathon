from __future__ import annotations

from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup


async def fetch_url(url: str) -> str:
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        resp = await client.get(url, headers={"User-Agent": "FuseKit-Integrator/1.0"})
        resp.raise_for_status()
        return resp.text


def html_to_text(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    return soup.get_text(separator="\n", strip=True)


async def fetch_docs_bundle(docs_url: str, max_pages: int = 3) -> str:
    html = await fetch_url(docs_url)
    soup = BeautifulSoup(html, "lxml")
    base_host = urlparse(docs_url).netloc

    pages = [html_to_text(html)]
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
        pages.append(html_to_text(sub_html))

    return "\n\n".join(pages)
