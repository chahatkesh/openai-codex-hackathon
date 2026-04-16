from __future__ import annotations
import json

from app.docs_fetcher import fetch_docs_bundle
from app.llm import LLMClient
from app.schemas import DiscoveryResult

SYSTEM_PROMPT = """You analyze API documentation pages. Return strict JSON with keys:
provider_name, base_url, auth_method, key_endpoints, rate_limits, sandbox_available.
auth_method must be one of: api_key, bearer, oauth, none, unknown.
"""

_VALID_AUTH_METHODS = {"api_key", "bearer", "oauth", "none", "unknown"}


def _coerce_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "yes", "1"}:
            return True
        if normalized in {"false", "no", "0", "unknown", "", "n/a", "none"}:
            return False
    return False


def _normalize_discovery_payload(data: dict) -> dict:
    normalized = dict(data)

    auth_method = str(normalized.get("auth_method", "unknown")).strip().lower()
    if auth_method not in _VALID_AUTH_METHODS:
        auth_method = "unknown"
    normalized["auth_method"] = auth_method

    key_endpoints = normalized.get("key_endpoints", [])
    if isinstance(key_endpoints, str):
        key_endpoints = [key_endpoints] if key_endpoints.strip() else []
    elif not isinstance(key_endpoints, list):
        key_endpoints = []
    normalized["key_endpoints"] = [str(item) for item in key_endpoints[:20]]

    rate_limits = normalized.get("rate_limits")
    if rate_limits is None:
        normalized["rate_limits"] = None
    elif isinstance(rate_limits, str):
        normalized["rate_limits"] = rate_limits
    else:
        normalized["rate_limits"] = json.dumps(rate_limits)

    normalized["sandbox_available"] = _coerce_bool(normalized.get("sandbox_available", False))

    provider_name = normalized.get("provider_name")
    if not provider_name:
        normalized["provider_name"] = "Unknown API"

    return normalized


async def run_discovery(docs_url: str, llm: LLMClient) -> DiscoveryResult:
    text = (await fetch_docs_bundle(docs_url, max_pages=2))[:16000]
    prompt = f"Docs URL: {docs_url}\n\nDocumentation text:\n{text}"
    data = await llm.generate_json(SYSTEM_PROMPT, prompt)
    return DiscoveryResult.model_validate(_normalize_discovery_payload(data))
