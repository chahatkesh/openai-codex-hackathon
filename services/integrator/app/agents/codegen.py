from __future__ import annotations
from pathlib import Path
import re

from app.llm import LLMClient
from app.schemas import APISpecification, GeneratedTool


def _find_tool_schema_path() -> Path:
    current = Path(__file__).resolve()
    for parent in current.parents:
        candidate = parent / "packages" / "contracts" / "tool-definition.schema.json"
        if candidate.exists():
            return candidate
    return current.parents[2] / "tool-definition.schema.json"


TOOL_SCHEMA_PATH = _find_tool_schema_path()

SYSTEM_PROMPT = """Generate a FuseKit tool definition and executable python source.
Return strict JSON with keys:
name, description, provider, cost_per_call, status, category,
input_schema, output_schema, source, version, implementation_module, python_code.
python_code must define: async def execute(**kwargs) -> str
"""

MANAGED_PROVIDER_REQUIREMENTS: dict[str, list[str]] = {
    "twilio": ["TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_FROM_NUMBER"],
    "slack": ["SLACK_BOT_TOKEN"],
    "resend": ["RESEND_API_KEY"],
}

PUBLIC_INPUT_ALLOWLIST = {
    "to",
    "message",
    "text",
    "channel",
    "body",
    "subject",
    "url",
    "query",
    "count",
    "category",
    "email",
    "recipient",
    "title",
    "content",
}

INTERNAL_FIELD_TOKENS = {
    "token",
    "secret",
    "apikey",
    "api_key",
    "auth",
    "password",
    "accountsid",
    "fromnumber",
    "messagingservicesid",
    "senderid",
    "clientsecret",
}


def _sanitize_tool_name(name: str) -> str:
    raw = "".join(ch.lower() if ch.isalnum() else "_" for ch in name).strip("_")
    if not raw:
        return "generated_tool"
    if raw[0].isdigit():
        raw = f"tool_{raw}"
    return raw


def _normalize_provider_name(name: str | None) -> str:
    raw = "".join(ch.lower() if ch.isalnum() else "_" for ch in (name or "")).strip("_")
    return raw


def _requires_credentials(api_spec: APISpecification) -> bool:
    auth = api_spec.auth or {}
    auth_type = str(auth.get("type") or auth.get("method") or "").strip().lower()
    return auth_type not in {"", "none", "unknown"}


def _is_managed_provider(api_spec: APISpecification) -> bool:
    return _normalize_provider_name(api_spec.provider_name) in MANAGED_PROVIDER_REQUIREMENTS


def _field_normalized(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", name.lower())


def _managed_secret_field_names(api_spec: APISpecification) -> set[str]:
    provider = _normalize_provider_name(api_spec.provider_name)
    names: set[str] = set()
    for key in MANAGED_PROVIDER_REQUIREMENTS.get(provider, []):
        key_lower = key.lower()
        names.add(_field_normalized(key_lower))
        if key_lower.startswith(f"{provider}_"):
            names.add(_field_normalized(key_lower[len(provider) + 1 :]))
    for key in (api_spec.auth or {}).keys():
        names.add(_field_normalized(key))
    return names


def _sanitize_public_input_schema(schema: dict, api_spec: APISpecification) -> dict:
    if not _is_managed_provider(api_spec):
        return schema

    properties = dict(schema.get("properties", {}))
    required = list(schema.get("required", []))
    secret_names = _managed_secret_field_names(api_spec)

    kept_properties: dict = {}
    kept_required: list[str] = []
    for field_name, field_schema in properties.items():
        normalized = _field_normalized(field_name)
        should_hide = (
            normalized in secret_names
            or (
                any(token in normalized for token in INTERNAL_FIELD_TOKENS)
                and normalized not in PUBLIC_INPUT_ALLOWLIST
            )
        )
        if should_hide:
            continue
        kept_properties[field_name] = field_schema
        if field_name in required:
            kept_required.append(field_name)

    next_schema = dict(schema)
    next_schema["properties"] = kept_properties
    next_schema["required"] = kept_required
    return next_schema


def _managed_provider_prompt(api_spec: APISpecification) -> str:
    provider = _normalize_provider_name(api_spec.provider_name)
    if provider in MANAGED_PROVIDER_REQUIREMENTS:
        requirement_list = ", ".join(MANAGED_PROVIDER_REQUIREMENTS[provider])
        base = (
            "\nManaged provider policy:\n"
            f"- {api_spec.provider_name} is credential-managed by FuseKit.\n"
            "- Do NOT expose provider secrets, auth tokens, API keys, or provider-owned configuration in the public input schema.\n"
            "- The public FuseKit-facing schema must only expose end-user inputs that the deployed app should provide.\n"
            "- Resolve provider credentials internally at runtime using app.services.provider_credentials.get_provider_credentials(provider_name).\n"
            f"- Provider-managed credential keys stay internal to FuseKit: {requirement_list}.\n"
        )
    else:
        base = ""
    if provider == "twilio":
        return base + (
            "- Do NOT expose AccountSid, AuthToken, From, MessagingServiceSid, or other provider-owned secrets/config in the public input schema.\n"
            "- The public FuseKit-facing schema must only expose end-user inputs: `to` and `message`.\n"
            "- Resolve Twilio credentials internally at runtime using app.services.provider_credentials.get_provider_credentials('twilio').\n"
            "- Return JSON as a string describing success/failure, e.g. {\"ok\": true, \"sid\": \"...\", \"message\": \"...\"}.\n"
        )
    return base


def _twilio_managed_tool(tool_name: str) -> dict:
    python_code = """
import json
from base64 import b64encode

import httpx

from app.config import settings
from app.services.provider_credentials import get_provider_credentials


async def execute(to: str, message: str) -> str:
    creds = await get_provider_credentials("twilio")
    account_sid = creds.get("TWILIO_ACCOUNT_SID") or settings.twilio_account_sid
    auth_token = creds.get("TWILIO_AUTH_TOKEN") or settings.twilio_auth_token
    from_number = creds.get("TWILIO_FROM_NUMBER") or settings.twilio_from_number

    if not account_sid or not auth_token or not from_number:
        return "ERROR: Twilio credentials not configured in FuseKit. Add TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, and TWILIO_FROM_NUMBER in /credentials."

    url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"
    auth_str = b64encode(f"{account_sid}:{auth_token}".encode()).decode()

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                url,
                headers={"Authorization": f"Basic {auth_str}"},
                data={
                    "To": to,
                    "From": from_number,
                    "Body": message,
                },
            )
            resp.raise_for_status()
            data = resp.json()
        return json.dumps(
            {
                "ok": True,
                "sid": data.get("sid", "unknown"),
                "status": data.get("status"),
                "message": "SMS sent successfully",
            }
        )
    except Exception as exc:
        return json.dumps(
            {
                "ok": False,
                "error": str(exc),
            }
        )
""".strip()

    return {
        "name": tool_name,
        "description": "Send an SMS or MMS message using Twilio through FuseKit-managed credentials.",
        "provider": "Twilio",
        "cost_per_call": 20,
        "status": "pending_credentials",
        "category": "communication",
        "input_schema": {
            "type": "object",
            "required": ["to", "message"],
            "properties": {
                "to": {
                    "type": "string",
                    "description": "Recipient phone number in E.164 format, e.g. +1234567890.",
                },
                "message": {
                    "type": "string",
                    "description": "SMS message body.",
                },
            },
            "additionalProperties": False,
        },
        "output_schema": {
            "type": "object",
            "properties": {
                "ok": {"type": "boolean"},
                "sid": {"type": "string"},
                "status": {"type": "string"},
                "message": {"type": "string"},
                "error": {"type": "string"},
            },
        },
        "source": "pipeline",
        "version": 1,
        "implementation_module": f"{tool_name}_module",
        "python_code": python_code + "\n",
    }


def _apply_managed_provider_policy(data: dict, api_spec: APISpecification, tool_name: str) -> dict:
    provider = _normalize_provider_name(api_spec.provider_name)
    if provider == "twilio":
        managed = _twilio_managed_tool(tool_name)
        data.update(managed)
        return data
    if _is_managed_provider(api_spec):
        data["input_schema"] = _sanitize_public_input_schema(
            data.get("input_schema", {"type": "object", "properties": {}, "required": []}),
            api_spec,
        )
    return data


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
        f"{_managed_provider_prompt(api_spec)}"
    )

    data = await llm.generate_json(SYSTEM_PROMPT, prompt)
    data.setdefault("name", tool_name)
    data["name"] = _sanitize_tool_name(str(data["name"]))
    data = _apply_managed_provider_policy(data, api_spec, tool_name)
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
