"""get_producthunt — Get trending products from Product Hunt."""

import json

import httpx

from app.config import settings
from app.tools import registry


async def execute(category: str = "tech", count: int = 5) -> str:
    """Get today's trending products from Product Hunt.

    Falls back to scraping if API token is not set.
    """
    if settings.producthunt_api_token:
        return await _via_api(category, count)
    return await _via_scrape(count)


async def _via_api(category: str, count: int) -> str:
    query = """
    query {
      posts(first: %d, order: VOTES) {
        edges {
          node {
            name
            tagline
            url
            votesCount
            website
          }
        }
      }
    }
    """ % min(count, 20)

    async with httpx.AsyncClient(timeout=15, verify=False) as client:
        resp = await client.post(
            "https://api.producthunt.com/v2/api/graphql",
            headers={
                "Authorization": f"Bearer {settings.producthunt_api_token}",
                "Content-Type": "application/json",
            },
            json={"query": query},
        )
        resp.raise_for_status()
        data = resp.json()

    posts = []
    for edge in data.get("data", {}).get("posts", {}).get("edges", []):
        node = edge["node"]
        posts.append({
            "name": node["name"],
            "tagline": node["tagline"],
            "url": node["url"],
            "votes": node["votesCount"],
            "website": node.get("website", ""),
        })

    return json.dumps(posts, indent=2)


async def _via_scrape(count: int) -> str:
    """Fallback: scrape Product Hunt homepage."""
    from bs4 import BeautifulSoup

    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        resp = await client.get(
            "https://www.producthunt.com",
            headers={"User-Agent": "FuseKit/1.0"},
        )
        resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "lxml")
    text = soup.get_text(separator="\n", strip=True)

    # Return raw text since parsing PH's React DOM is fragile
    if len(text) > 5000:
        text = text[:5000] + "\n\n[...truncated]"

    return f"Product Hunt homepage content (scraped):\n\n{text}"


registry.register("get_producthunt", execute)
