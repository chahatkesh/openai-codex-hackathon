from __future__ import annotations
from pathlib import Path

from app.llm import LLMClient
from app.schemas import APISpecification, GeneratedTool

TOOL_SCHEMA_PATH = Path(__file__).resolve().parents[4] / "packages" / "contracts" / "tool-definition.schema.json"

SYSTEM_PROMPT = """Generate a FuseKit tool definition and executable python source.
Return strict JSON with keys:
name, description, provider, cost_per_call, status, category,
input_schema, output_schema, source, version, implementation_module, python_code.
python_code must define: async def execute(**kwargs) -> str
"""


def _sanitize_tool_name(name: str) -> str:
    raw = "".join(ch.lower() if ch.isalnum() else "_" for ch in name).strip("_")
    if not raw:
        return "generated_tool"
    if raw[0].isdigit():
        raw = f"tool_{raw}"
    return raw


def _requires_credentials(api_spec: APISpecification) -> bool:
    auth = api_spec.auth or {}
    auth_type = str(auth.get("type") or auth.get("method") or "").strip().lower()
    return auth_type not in {"", "none", "unknown"}


async def run_codegen(
    api_spec: APISpecification,
    requested_tool_name: str | None,
    llm: LLMClient,
) -> GeneratedTool:
    schema_text = TOOL_SCHEMA_PATH.read_text(encoding="utf-8") if TOOL_SCHEMA_PATH.exists() else "{}"

    tool_name = _sanitize_tool_name(requested_tool_name or f"{api_spec.provider_name}_tool")
    prompt = (
        f"Requested tool name: {tool_name}\n"
        f"API specification JSON:\n{api_spec.model_dump_json(indent=2)}\n\n"
        f"Tool definition schema:\n{schema_text}\n\n"
        "Implementation constraints:\n"
        "- Use httpx AsyncClient\n"
        "- Prefer provider credentials via app.services.provider_credentials.get_provider_credentials(provider_name)\n"
        "- Fall back to env vars only if provider credentials are unavailable\n"
        "- Return string output\n"
        "- Include basic error handling"
    )

    data = await llm.generate_json(SYSTEM_PROMPT, prompt)
    data.setdefault("name", tool_name)
    data["name"] = _sanitize_tool_name(str(data["name"]))
    data.setdefault("source", "pipeline")
    data.setdefault("version", 1)
    data.setdefault("status", "pending_credentials" if _requires_credentials(api_spec) else "live")
    data.setdefault("category", "other")
    data.setdefault("cost_per_call", 10)
    data.setdefault("provider", api_spec.provider_name)
    data.setdefault("description", f"Auto-generated tool for {api_spec.provider_name}")
    data.setdefault(
        "input_schema",
        {"type": "object", "properties": {}, "additionalProperties": True},
    )
    data.setdefault("output_schema", {"type": "object", "properties": {"result": {"type": "string"}}})
    data.setdefault("implementation_module", f"app.tools.{data['name']}.execute")
    if _requires_credentials(api_spec) and data.get("status") == "live":
        data["status"] = "pending_credentials"

    code = data.get("python_code", "")
    if "async def execute" not in code:
        data["python_code"] = (
            "import json\n"
            "\n"
            "async def execute(**kwargs) -> str:\n"
            "    return json.dumps(kwargs)\n"
        )

    return GeneratedTool.model_validate(data)
