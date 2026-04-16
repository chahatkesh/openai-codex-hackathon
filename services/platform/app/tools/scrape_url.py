"""scrape_url — Scrape a webpage and return structured text content."""

from __future__ import annotations

import json
from io import BytesIO
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from app.tools import registry

try:
    import yaml
except ImportError:  # pragma: no cover - optional dependency in some dev envs
    yaml = None

try:
    from pypdf import PdfReader
except ImportError:  # pragma: no cover - optional dependency in some dev envs
    PdfReader = None


def _truncate_text(text: str, limit: int = 10_000) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + "\n\n[...truncated]"


def _detect_content_type(url: str, content_type: str | None, body: bytes) -> str:
    ctype = (content_type or "").split(";")[0].strip().lower()
    if ctype:
        return ctype
    lower = url.lower()
    if lower.endswith(".pdf"):
        return "application/pdf"
    if lower.endswith(".yaml") or lower.endswith(".yml"):
        return "application/yaml"
    if lower.endswith(".json"):
        return "application/json"
    if body.lstrip().startswith(b"%PDF-"):
        return "application/pdf"
    if body.lstrip().startswith((b"{", b"[")):
        return "application/json"
    return "text/html"


def _is_probably_openapi(url: str, text: str) -> bool:
    lowered = text.lower()
    return any(token in url.lower() for token in ("openapi", "swagger")) or (
        '"openapi"' in lowered or lowered.lstrip().startswith("openapi:")
    )


def _html_payload(url: str, html: str) -> dict:
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "noscript", "svg", "nav", "footer", "header", "aside"]):
        tag.decompose()

    main = (
        soup.find("main")
        or soup.find("article")
        or soup.find(attrs={"role": "main"})
        or soup.body
        or soup
    )

    title = ""
    if soup.title and soup.title.string:
        title = " ".join(soup.title.string.split())
    if not title:
        first_heading = main.find(["h1", "h2"])
        if first_heading:
            title = " ".join(first_heading.get_text(" ", strip=True).split())
    if not title:
        title = url

    headings = []
    for tag in main.find_all(["h1", "h2", "h3"])[:20]:
        text = " ".join(tag.get_text(" ", strip=True).split())
        if text:
            headings.append(text)

    code_blocks = []
    for tag in main.find_all(["pre", "code"])[:20]:
        text = tag.get_text("\n", strip=True)
        if text:
            code_blocks.append(text)

    links = []
    for anchor in main.find_all("a", href=True):
        href = anchor.get("href")
        if not href:
            continue
        absolute = urljoin(url, href)
        if absolute not in links:
            links.append(absolute)
        if len(links) >= 25:
            break

    text = main.get_text(separator="\n", strip=True)
    text = _truncate_text(text)
    lines = [" ".join(line.split()) for line in text.splitlines() if line.strip()]
    endpoint_hints = [
        line for line in lines
        if any(method in line for method in ("GET ", "POST ", "PUT ", "PATCH ", "DELETE "))
    ][:20]
    auth_hints = [
        line for line in lines
        if any(token in line.lower() for token in ("bearer", "api key", "authorization", "oauth"))
    ][:10]

    return {
        "url": url,
        "content_type": "text/html",
        "title": title,
        "summary": lines[0] if lines else "",
        "text": text,
        "headings": headings,
        "code_blocks": code_blocks,
        "links": links,
        "endpoint_hints": endpoint_hints,
        "auth_hints": auth_hints,
    }


def _openapi_payload(url: str, text: str) -> dict:
    payload = None
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        if yaml is not None:
            payload = yaml.safe_load(text)

    if not isinstance(payload, dict):
        return {
            "url": url,
            "content_type": "application/openapi",
            "title": url,
            "text": _truncate_text(text),
        }

    info = payload.get("info") or {}
    title = info.get("title") or payload.get("openapi") or payload.get("swagger") or url
    servers = payload.get("servers") or []
    base_url = ""
    if servers and isinstance(servers[0], dict):
        base_url = str(servers[0].get("url") or "")

    endpoints = []
    for path, methods in list((payload.get("paths") or {}).items())[:40]:
        if not isinstance(methods, dict):
            continue
        for method in methods:
            endpoints.append({"method": str(method).upper(), "path": path})

    components = payload.get("components")
    if not isinstance(components, dict):
        components = {}

    return {
        "url": url,
        "content_type": "application/openapi",
        "title": str(title),
        "base_url": base_url,
        "endpoints": endpoints[:25],
        "auth": components.get("securitySchemes", {}),
        "text": json.dumps(
            {"title": title, "base_url": base_url, "endpoints": endpoints[:25]},
            indent=2,
        ),
    }


def _pdf_payload(url: str, body: bytes) -> dict:
    if PdfReader is None:
        return {
            "url": url,
            "content_type": "application/pdf",
            "title": url,
            "text": "PDF support requires the pypdf package to be installed.",
        }

    reader = PdfReader(BytesIO(body))
    pages = []
    for page_number, page in enumerate(reader.pages[:20], start=1):
        text = (page.extract_text() or "").strip()
        pages.append({"page": page_number, "text": text})

    combined = "\n\n".join(
        f"[Page {item['page']}]\n{item['text']}" for item in pages if item["text"]
    )
    return {
        "url": url,
        "content_type": "application/pdf",
        "title": str(((reader.metadata or {}).get("/Title")) or url),
        "pages": pages,
        "text": _truncate_text(combined or "No extractable text found in PDF."),
    }


async def execute(url: str) -> str:
    """Fetch a URL and return structured scrape output as JSON text."""
    async with httpx.AsyncClient(timeout=30, follow_redirects=True, verify=False) as client:
        resp = await client.get(url, headers={"User-Agent": "FuseKit/1.0"})
        resp.raise_for_status()

    final_url = str(resp.url)
    body = resp.content
    content_type = _detect_content_type(final_url, resp.headers.get("content-type"), body)

    if content_type == "text/html":
        payload = _html_payload(final_url, body.decode(resp.encoding or "utf-8", errors="ignore"))
    elif content_type == "application/pdf":
        payload = _pdf_payload(final_url, body)
    else:
        text = body.decode(resp.encoding or "utf-8", errors="ignore")
        if content_type in {"application/json", "application/yaml", "text/plain"} and _is_probably_openapi(final_url, text):
            payload = _openapi_payload(final_url, text)
        else:
            payload = {
                "url": final_url,
                "content_type": content_type,
                "title": final_url,
                "text": _truncate_text(text),
            }

    payload["metadata"] = {
        "status_code": resp.status_code,
        "final_url": final_url,
    }
    return json.dumps(payload, indent=2)


registry.register("scrape_url", execute)
