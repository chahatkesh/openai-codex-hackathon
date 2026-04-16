"""search_web — Search the web using Serper (Google Search API)."""

import json

import httpx

from app.config import settings
from app.tools import registry


async def execute(query: str, num_results: int = 5) -> str:
    """Search the web and return top results."""
    if not settings.serper_api_key:
        return "ERROR: Serper API key not configured. Set SERPER_API_KEY in .env"

    async with httpx.AsyncClient(timeout=15, verify=False) as client:
        resp = await client.post(
            "https://google.serper.dev/search",
            headers={
                "X-API-KEY": settings.serper_api_key,
                "Content-Type": "application/json",
            },
            json={"q": query, "num": min(num_results, 10)},
        )
        resp.raise_for_status()
        data = resp.json()

    results = []
    for item in data.get("organic", [])[:num_results]:
        results.append({
            "title": item.get("title", ""),
            "url": item.get("link", ""),
            "snippet": item.get("snippet", ""),
        })

    return json.dumps(results, indent=2)


registry.register("search_web", execute)
