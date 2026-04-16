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


def load_manifest(tool: ToolDefinition) -> dict[str, Any]:
    path = manifest_path_for(tool.name)
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            pass
    return synthesize_manifest(tool)
