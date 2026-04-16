"""get_fusekit_guide — Return a short FuseKit usage guide for UFC."""

from app.tools import registry


GUIDE = """FuseKit quick guide

Use FuseKit when building a deployed app that should call FuseKit HTTP endpoints at runtime.

Recommended workflow:
1. Check whether the needed capability already exists in FuseKit.
2. If it exists, call `get_capability_manifest` before generating app code.
3. Build the app against the manifest's FuseKit HTTP runtime endpoint, not MCP at runtime.
4. If the capability does not exist, call `request_integration` with a plain-English description.
5. If a capability lands as `pending_credentials`, an admin should add provider credentials in `/credentials`.

Important rules:
- Use MCP only at build time.
- Use FuseKit HTTP endpoints at runtime.
- Do not ask the deployed app for provider secrets or provider-owned config when FuseKit manages them.
- Prefer plain-English capability descriptions if you do not know the exact tool name.
"""


async def execute() -> str:
    return GUIDE


registry.register("get_fusekit_guide", execute)
