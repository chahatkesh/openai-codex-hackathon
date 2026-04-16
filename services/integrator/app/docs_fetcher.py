from __future__ import annotations

import json
from dataclasses import dataclass, field
from io import BytesIO
from typing import Any
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from app.config import settings

try:
    import yaml
except ImportError:  # pragma: no cover - optional dependency in some dev envs
    yaml = None

try:
    from pypdf import PdfReader
except ImportError:  # pragma: no cover - optional dependency in some dev envs
    PdfReader = None


@dataclass(slots=True)
class DocumentPage:
    url: str
    content_type: str
    title: str
    text: str
    headings: list[str] = field(default_factory=list)
    code_blocks: list[str] = field(default_factory=list)
    links: list[str] = field(default_factory=list)
    endpoint_hints: list[str] = field(default_factory=list)
    auth_hints: list[str] = field(default_factory=list)
    rate_limit_hints: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


def html_to_text(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "noscript", "svg"]):
        tag.decompose()
    text = soup.get_text(separator="\n", strip=True)
    return _truncate_text(text, 12_000)


def _truncate_text(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + "\n\n[...truncated]"


def _clean_text(value: str) -> str:
    return " ".join(value.split())


def _detect_content_type(url: str, content_type: str | None, body: bytes) -> str:
    ctype = (content_type or "").split(";")[0].strip().lower()
    if ctype:
        return ctype

    parsed = urlparse(url)
    path = parsed.path.lower()
    if path.endswith(".pdf"):
        return "application/pdf"
    if path.endswith(".json"):
        return "application/json"
    if path.endswith(".yaml") or path.endswith(".yml"):
        return "application/yaml"

    stripped = body.lstrip()
    if stripped.startswith(b"%PDF-"):
        return "application/pdf"
    if stripped.startswith((b"{", b"[")):
        return "application/json"
    return "text/html"


def _is_probably_openapi(url: str, text: str) -> bool:
    lower_url = url.lower()
    if any(token in lower_url for token in ("openapi", "swagger")):
        return True

    lowered = text.lower()
    return '"openapi"' in lowered or lowered.lstrip().startswith("openapi:")


def _parse_html_page(url: str, html: str) -> DocumentPage:
    soup = BeautifulSoup(html, "lxml")

    # Remove chrome and noisy layout containers first.
    for tag in soup([
        "script",
        "style",
        "noscript",
        "svg",
        "nav",
        "footer",
        "header",
        "aside",
        "form",
    ]):
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
        title = _clean_text(soup.title.string)
    if not title:
        heading = main.find(["h1", "h2"])
        if heading:
            title = _clean_text(heading.get_text(" ", strip=True))
    if not title:
        title = url

    headings = [
        _clean_text(tag.get_text(" ", strip=True))
        for tag in main.find_all(["h1", "h2", "h3"])[:20]
        if tag.get_text(strip=True)
    ]

    code_blocks = [
        block.get_text("\n", strip=True)
        for block in main.find_all(["pre", "code"])[:20]
        if block.get_text(strip=True)
    ]

    links: list[str] = []
    for anchor in main.find_all("a", href=True):
        href = anchor.get("href")
        if not href:
            continue
        absolute = urljoin(url, href)
        if absolute not in links:
            links.append(absolute)
        if len(links) >= 25:
            break

    text = html_to_text(str(main))
    lines = [_clean_text(line) for line in text.splitlines() if _clean_text(line)]
    endpoint_hints = [
        line for line in lines
        if any(method in line for method in ("GET ", "POST ", "PUT ", "PATCH ", "DELETE "))
    ][:20]
    auth_hints = [
        line for line in lines
        if any(token in line.lower() for token in ("api key", "bearer", "authorization", "oauth"))
    ][:12]
    rate_limit_hints = [
        line for line in lines
        if "rate limit" in line.lower() or "requests per" in line.lower()
    ][:12]

    return DocumentPage(
        url=url,
        content_type="text/html",
        title=title,
        text=text,
        headings=headings,
        code_blocks=code_blocks if settings.docs_fetch_extract_code_blocks else [],
        links=links,
        endpoint_hints=endpoint_hints,
        auth_hints=auth_hints,
        rate_limit_hints=rate_limit_hints,
        metadata={"link_count": len(links)},
    )


def _parse_openapi_document(url: str, text: str) -> DocumentPage:
    payload: dict[str, Any] | None = None
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        if yaml is not None:
            loaded = yaml.safe_load(text)
            if isinstance(loaded, dict):
                payload = loaded

    if payload is None:
        return DocumentPage(
            url=url,
            content_type="application/openapi",
            title=url,
            text=_truncate_text(text, 12_000),
        )

    info = payload.get("info") or {}
    servers = payload.get("servers") or []
    title = info.get("title") or payload.get("openapi") or payload.get("swagger") or url
    base_url = ""
    if servers and isinstance(servers, list) and isinstance(servers[0], dict):
        base_url = str(servers[0].get("url") or "")

    endpoint_hints = []
    paths = payload.get("paths") or {}
    if isinstance(paths, dict):
        for path, methods in list(paths.items())[:40]:
            if not isinstance(methods, dict):
                continue
            for method in methods.keys():
                endpoint_hints.append(f"{str(method).upper()} {path}")

    auth_hints = []
    components = payload.get("components")
    if not isinstance(components, dict):
        components = {}
    security_schemes = components.get("securitySchemes") if isinstance(components, dict) else None
    if isinstance(security_schemes, dict):
        for name, scheme in security_schemes.items():
            if not isinstance(scheme, dict):
                continue
            auth_hints.append(
                f"{name}: type={scheme.get('type', 'unknown')} scheme={scheme.get('scheme', '')}".strip()
            )

    summary = {
        "title": title,
        "base_url": base_url,
        "endpoint_count": len(endpoint_hints),
        "auth": auth_hints,
        "paths": endpoint_hints[:25],
    }

    return DocumentPage(
        url=url,
        content_type="application/openapi",
        title=str(title),
        text=json.dumps(summary, indent=2),
        headings=[str(title), "Paths", "Authentication"],
        endpoint_hints=endpoint_hints[:25],
        auth_hints=auth_hints[:10],
        metadata={"base_url": base_url, "raw_path_count": len(endpoint_hints)},
    )


def _parse_pdf_document(url: str, content: bytes) -> DocumentPage:
    if PdfReader is None:
        return DocumentPage(
            url=url,
            content_type="application/pdf",
            title=url,
            text="PDF support requires the pypdf package to be installed.",
        )

    reader = PdfReader(BytesIO(content))
    page_chunks = []
    for index, page in enumerate(reader.pages[:20], start=1):
        extracted = (page.extract_text() or "").strip()
        if extracted:
            page_chunks.append(f"[Page {index}]\n{extracted}")

    combined = "\n\n".join(page_chunks) if page_chunks else "No extractable text found in PDF."
    title = ""
    try:
        title = str((reader.metadata or {}).get("/Title") or "")
    except Exception:  # pragma: no cover - metadata shape varies
        title = ""

    return DocumentPage(
        url=url,
        content_type="application/pdf",
        title=title or url,
        text=_truncate_text(combined, 20_000),
        headings=[title] if title else [],
        metadata={"page_count": len(reader.pages)},
    )


async def _render_with_playwright(url: str) -> str | None:
    try:
        from playwright.async_api import async_playwright
    except ImportError:  # pragma: no cover - optional dependency in some dev envs
        return None

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        try:
            page = await browser.new_page()
            await page.goto(url, wait_until="networkidle", timeout=settings.docs_fetch_render_timeout_seconds * 1000)
            return await page.content()
        finally:
            await browser.close()


def _needs_js_render(html: str) -> bool:
    text = html_to_text(html)
    lowered = text.lower()
    if len(text) < 300:
        return True
    return any(
        marker in lowered
        for marker in (
            "enable javascript",
            "javascript required",
            "loading...",
            "please wait",
        )
    )


async def fetch_url(url: str) -> str:
    async with httpx.AsyncClient(timeout=settings.docs_fetch_timeout_seconds, follow_redirects=True) as client:
        resp = await client.get(url, headers={"User-Agent": settings.docs_fetch_user_agent})
        resp.raise_for_status()
        body = resp.content[: settings.docs_fetch_max_bytes]
        content_type = _detect_content_type(str(resp.url), resp.headers.get("content-type"), body)
        if content_type == "text/html":
            html = body.decode(resp.encoding or "utf-8", errors="ignore")
            if settings.docs_fetch_render_js and _needs_js_render(html):
                rendered = await _render_with_playwright(str(resp.url))
                if rendered:
                    return rendered
            return html
        return body.decode(resp.encoding or "utf-8", errors="ignore")


async def fetch_document(url: str) -> DocumentPage:
    async with httpx.AsyncClient(timeout=settings.docs_fetch_timeout_seconds, follow_redirects=True) as client:
        resp = await client.get(url, headers={"User-Agent": settings.docs_fetch_user_agent})
        resp.raise_for_status()
        final_url = str(resp.url)
        body = resp.content[: settings.docs_fetch_max_bytes]
        content_type = _detect_content_type(final_url, resp.headers.get("content-type"), body)

    if content_type == "text/html":
        html = body.decode(resp.encoding or "utf-8", errors="ignore")
        if settings.docs_fetch_render_js and _needs_js_render(html):
            rendered = await _render_with_playwright(final_url)
            if rendered:
                html = rendered
        page = _parse_html_page(final_url, html)
    elif content_type == "application/pdf" and settings.docs_fetch_parse_pdf:
        page = _parse_pdf_document(final_url, body)
    elif settings.docs_fetch_parse_openapi and (
        content_type in {"application/json", "application/yaml", "text/yaml", "text/plain"}
        or _is_probably_openapi(final_url, body.decode(resp.encoding or "utf-8", errors="ignore"))
    ):
        text = body.decode(resp.encoding or "utf-8", errors="ignore")
        page = _parse_openapi_document(final_url, text)
    else:
        text = body.decode(resp.encoding or "utf-8", errors="ignore")
        page = DocumentPage(
            url=final_url,
            content_type=content_type,
            title=final_url,
            text=_truncate_text(text, 12_000),
        )

    page.metadata.update(
        {
            "status_code": resp.status_code,
            "final_url": final_url,
        }
    )
    return page


def _candidate_links(page: DocumentPage) -> list[str]:
    if page.content_type != "text/html":
        return []

    keywords = (
        "auth",
        "authentication",
        "reference",
        "api-reference",
        "quickstart",
        "guide",
        "guides",
        "errors",
        "rate-limit",
        "rate_limits",
        "pagination",
        "openapi",
        "swagger",
    )
    ranked = []
    seen = set()
    base_host = urlparse(page.url).netloc
    for link in page.links:
        parsed = urlparse(link)
        if parsed.netloc != base_host or link in seen:
            continue
        seen.add(link)
        score = sum(keyword in link.lower() for keyword in keywords)
        if score > 0:
            ranked.append((score, link))
    ranked.sort(reverse=True)
    return [link for _, link in ranked[: max(settings.docs_fetch_max_pages - 1, 0)]]


def _format_page_bundle(page: DocumentPage) -> str:
    chunks = [
        f"Source URL: {page.url}",
        f"Type: {page.content_type}",
        f"Title: {page.title}",
    ]

    if page.metadata:
        metadata_summary = ", ".join(f"{key}={value}" for key, value in page.metadata.items())
        chunks.append(f"Metadata: {metadata_summary}")
    if page.headings:
        chunks.append("Important headings:\n- " + "\n- ".join(page.headings[:10]))
    if page.auth_hints:
        chunks.append("Auth hints:\n- " + "\n- ".join(page.auth_hints[:8]))
    if page.rate_limit_hints:
        chunks.append("Rate limit hints:\n- " + "\n- ".join(page.rate_limit_hints[:8]))
    if page.endpoint_hints:
        chunks.append("Endpoints found:\n- " + "\n- ".join(page.endpoint_hints[:15]))
    if page.code_blocks:
        chunks.append("Code examples:\n" + "\n\n".join(page.code_blocks[:5]))
    chunks.append("Clean content:\n" + page.text)
    return "\n\n".join(chunks)


async def fetch_docs_bundle(docs_url: str, max_pages: int | None = None) -> str:
    effective_max_pages = max_pages or settings.docs_fetch_max_pages

    root_page = await fetch_document(docs_url)
    pages = [root_page]
    seen = {root_page.url}

    for link in _candidate_links(root_page):
        if len(pages) >= effective_max_pages:
            break
        if link in seen:
            continue
        seen.add(link)
        try:
            pages.append(await fetch_document(link))
        except Exception:
            continue

    return "\n\n---\n\n".join(_format_page_bundle(page) for page in pages)
