"""scrape_url — Scrape a webpage and return its text content."""

import httpx
from bs4 import BeautifulSoup

from app.tools import registry


async def execute(url: str) -> str:
    """Fetch a URL and return the main text content."""
    async with httpx.AsyncClient(
        timeout=30, follow_redirects=True, verify=False
    ) as client:
        resp = await client.get(url, headers={"User-Agent": "FuseKit/1.0"})
        resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "lxml")

    # Remove script/style elements
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()

    text = soup.get_text(separator="\n", strip=True)

    # Truncate to ~8000 chars to stay within reasonable response size
    if len(text) > 8000:
        text = text[:8000] + "\n\n[...truncated]"

    return text


registry.register("scrape_url", execute)
