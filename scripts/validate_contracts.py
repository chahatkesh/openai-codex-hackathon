#!/usr/bin/env python3
"""Validate platform API responses against JSON contracts."""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any

import httpx

try:
    import jsonschema
except ModuleNotFoundError:
    jsonschema = None


API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
REPO_ROOT = Path(__file__).resolve().parents[1]
CONTRACTS_DIR = REPO_ROOT / "packages" / "contracts"


def _load_schema(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _validate(validator: Any, instance: Any, schema: dict[str, Any], label: str) -> None:
    validator(instance=instance, schema=schema)
    print(f"[PASS] {label}")


async def run() -> int:
    if jsonschema is None:
        print("jsonschema is required. Install it with: pip install jsonschema")
        return 2

    validate = jsonschema.validate

    wallet_schema = _load_schema(CONTRACTS_DIR / "wallet-response.schema.json")
    catalog_item_schema = _load_schema(CONTRACTS_DIR / "catalog-item.schema.json")
    integrate_request_schema = _load_schema(CONTRACTS_DIR / "integrate-request.schema.json")
    tool_call_error_schema = _load_schema(CONTRACTS_DIR / "tool-call-error.schema.json")

    async with httpx.AsyncClient(timeout=30) as client:
        # GET /api/wallet/balance
        balance_resp = await client.get(f"{API_BASE_URL}/api/wallet/balance")
        balance_resp.raise_for_status()
        _validate(validate, balance_resp.json(), wallet_schema, "GET /api/wallet/balance")

        # GET /api/catalog
        catalog_resp = await client.get(f"{API_BASE_URL}/api/catalog")
        catalog_resp.raise_for_status()
        catalog = catalog_resp.json()
        if not isinstance(catalog, list):
            raise AssertionError("GET /api/catalog must return a list")
        for idx, item in enumerate(catalog):
            _validate(validate, item, catalog_item_schema, f"GET /api/catalog item[{idx}]")

        # Validate integrate request payload shape locally (contract-level check).
        integrate_payload = {
            "docs_url": "https://example.com/docs",
            "requested_by": "user",
            "requested_tool_name": "sample_tool",
        }
        _validate(validate, integrate_payload, integrate_request_schema, "POST /api/integrate request payload")

        # Validate tool-call error contract locally.
        example_error = {
            "error_code": "TOOL_NOT_FOUND",
            "message": "TOOL_NOT_FOUND: missing_tool is not in catalog",
        }
        _validate(validate, example_error, tool_call_error_schema, "tool-call error schema")

    print("All contract validations passed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(asyncio.run(run()))
    except Exception as exc:
        print(f"[FAIL] {exc}")
        raise SystemExit(1)
