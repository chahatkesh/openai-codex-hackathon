from __future__ import annotations

from app.docs_fetcher import fetch_url, html_to_text
from app.llm import LLMClient
from app.schemas import DiscoveryResult

SYSTEM_PROMPT = """You analyze API documentation pages. Return strict JSON with keys:
provider_name, base_url, auth_method, key_endpoints, rate_limits, sandbox_available.
auth_method must be one of: api_key, bearer, oauth, none, unknown.
"""


async def run_discovery(docs_url: str, llm: LLMClient) -> DiscoveryResult:
    html = await fetch_url(docs_url)
    text = html_to_text(html)[:12000]
    prompt = f"Docs URL: {docs_url}\n\nDocumentation text:\n{text}"
    data = await llm.generate_json(SYSTEM_PROMPT, prompt)
    return DiscoveryResult.model_validate(data)
