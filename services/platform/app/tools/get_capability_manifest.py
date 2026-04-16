"""get_capability_manifest — Return the FuseKit runtime manifest for a capability."""

from __future__ import annotations

import json

from app.services.capabilities_service import get_tool_definition
from app.services.manifest_service import build_runtime_manifest
from app.tools import registry


async def execute(capability_name: str) -> str:
    tool = await get_tool_definition(capability_name)
    if tool is None:
        return (
            f"TOOL_NOT_FOUND: '{capability_name}' is not in the catalog. "
            "Request integration through FuseKit if this capability is required."
        )

    return json.dumps(build_runtime_manifest(tool), indent=2)


registry.register("get_capability_manifest", execute)
