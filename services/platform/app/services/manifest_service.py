from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.models import ToolDefinition

DYNAMIC_TOOLS_DIR = Path("/tmp/fusekit_dynamic_tools")
MANIFESTS_DIR = DYNAMIC_TOOLS_DIR / "manifests"


def manifest_path_for(tool_name: str) -> Path:
    return MANIFESTS_DIR / f"{tool_name}.json"


def build_manifest_pointer(tool_name: str) -> dict[str, str]:
    path = manifest_path_for(tool_name)
    return {
        "tool_name": tool_name,
        "manifest_path": str(path),
    }


def _build_example_request(schema: dict[str, Any]) -> dict[str, Any]:
    properties = schema.get("properties", {})
    required = schema.get("required", [])
    example: dict[str, Any] = {}

    for field in required:
        prop = properties.get(field, {})
        if "default" in prop:
            example[field] = prop["default"]
            continue
        prop_type = prop.get("type")
        if prop_type == "string":
            if "url" in field:
                example[field] = "https://example.com"
            elif "email" in field or field == "to":
                example[field] = "demo@example.com"
            elif "phone" in field:
                example[field] = "+10000000000"
            else:
                example[field] = "example"
        elif prop_type == "integer":
            example[field] = 1
        elif prop_type == "boolean":
            example[field] = False
        elif prop_type == "array":
            example[field] = []
        elif prop_type == "object":
            example[field] = {}
        else:
            example[field] = "example"

    return example


def synthesize_manifest(tool: ToolDefinition) -> dict[str, Any]:
    return {
        "tool_name": tool.name,
        "provider": tool.provider,
        "status": tool.status,
        "category": tool.category,
        "source": tool.source,
        "version": tool.version,
        "description": tool.description,
        "cost_per_call": tool.cost_per_call,
        "input_schema": tool.input_schema,
        "output_schema": tool.output_schema,
        "implementation_module": tool.implementation_module,
        "manifest_path": str(manifest_path_for(tool.name)),
    }


def build_runtime_manifest(tool: ToolDefinition) -> dict[str, Any]:
    base = load_manifest(tool)
    manifest = dict(base)

    manifest["tool_name"] = tool.name
    manifest["name"] = tool.name
    manifest["description"] = tool.description
    manifest["provider"] = tool.provider
    manifest["status"] = tool.status
    manifest["category"] = tool.category
    manifest["source"] = tool.source
    manifest["version"] = tool.version
    manifest["input_schema"] = tool.input_schema
    manifest["output_schema"] = tool.output_schema
    manifest["implementation_module"] = tool.implementation_module
    manifest["runtime_endpoint"] = {
        "method": "POST",
        "path": f"/api/execute/{tool.name}",
    }
    manifest["billing"] = {
        "cost_per_call": tool.cost_per_call,
        "currency": "credits",
    }
    manifest["auth"] = {
        "type": "bearer",
        "header": "Authorization",
        "format": "Bearer <fusekit_token>",
    }
    manifest["example_request"] = _build_example_request(tool.input_schema)
    manifest["manifest_pointer"] = build_manifest_pointer(tool.name)
    return manifest


def load_manifest(tool: ToolDefinition) -> dict[str, Any]:
    path = manifest_path_for(tool.name)
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            pass
    return synthesize_manifest(tool)
