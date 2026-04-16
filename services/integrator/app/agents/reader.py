from __future__ import annotations

from app.docs_fetcher import fetch_docs_bundle
from app.llm import LLMClient
from app.schemas import APISpecification, DiscoveryResult

SYSTEM_PROMPT = """Extract API specifications from docs and return strict JSON:
{
  "provider_name": str,
  "base_url": str|null,
  "auth": object,
  "endpoints": [{"path": str, "method": str, "required_params": array, "optional_params": array, "request_body": object, "response": object}],
  "errors": [{"code": str, "description": str}]
}
"""


async def run_reader(docs_url: str, discovery: DiscoveryResult, llm: LLMClient) -> APISpecification:
    bundle = await fetch_docs_bundle(docs_url)
    prompt = (
        f"Docs URL: {docs_url}\n"
        f"Discovery context: {discovery.model_dump_json()}\n\n"
        f"Documentation bundle:\n{bundle[:28000]}"
    )
    data = await llm.generate_json(SYSTEM_PROMPT, prompt)
    if "provider_name" not in data:
        data["provider_name"] = discovery.provider_name
    if "base_url" not in data:
        data["base_url"] = discovery.base_url
    return APISpecification.model_validate(data)
