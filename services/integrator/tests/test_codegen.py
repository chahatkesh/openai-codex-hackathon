from __future__ import annotations

import pytest

from app.agents.codegen import run_codegen
from app.schemas import APISpecification


class FakeLLM:
    async def generate_json(self, _system_prompt: str, _user_prompt: str):
        return {
            "name": "email_sender",
            "description": "Send an email",
            "provider": "Example API",
            "cost_per_call": 15,
            "status": "live",
            "category": "communication",
            "input_schema": {
                "type": "object",
                "properties": {"to": {"type": "string"}},
                "required": ["to"],
            },
            "output_schema": {"type": "object", "properties": {"result": {"type": "string"}}},
            "source": "pipeline",
            "version": 1,
            "implementation_module": "app.tools.email_sender.execute",
            "python_code": "async def execute(**kwargs) -> str:\n    return 'ok'\n",
        }


class ManagedProviderLLM:
    async def generate_json(self, _system_prompt: str, _user_prompt: str):
        return {
            "name": "send_slack_message_v3",
            "description": "Send a Slack message",
            "provider": "Slack",
            "cost_per_call": 10,
            "status": "live",
            "category": "communication",
            "input_schema": {
                "type": "object",
                "properties": {
                    "channel": {"type": "string"},
                    "text": {"type": "string"},
                    "token": {"type": "string"},
                    "bot_token": {"type": "string"},
                },
                "required": ["channel", "text", "token"],
            },
            "output_schema": {"type": "object", "properties": {"ok": {"type": "boolean"}}},
            "source": "pipeline",
            "version": 1,
            "implementation_module": "app.tools.send_slack_message_v3.execute",
            "python_code": "async def execute(**kwargs) -> str:\n    return 'ok'\n",
        }


@pytest.mark.asyncio
async def test_codegen_returns_valid_generated_tool():
    spec = APISpecification(provider_name="Example API")

    generated = await run_codegen(spec, "Email Sender", FakeLLM())

    assert generated.name == "email_sender"
    assert "async def execute" in generated.python_code
    assert generated.source == "pipeline"


@pytest.mark.asyncio
async def test_codegen_marks_auth_required_tools_pending_credentials():
    spec = APISpecification(provider_name="Example API", auth={"type": "bearer"})

    generated = await run_codegen(spec, "Email Sender", FakeLLM())

    assert generated.status == "pending_credentials"


@pytest.mark.asyncio
async def test_codegen_normalizes_twilio_to_fusekit_managed_contract():
    spec = APISpecification(provider_name="Twilio", auth={"type": "basic"})

    generated = await run_codegen(spec, "Send Twilio SMS V2", FakeLLM())

    assert generated.name == "send_twilio_sms_v2"
    assert generated.status == "pending_credentials"
    assert generated.input_schema["required"] == ["to", "message"]
    assert "AccountSid" not in generated.input_schema["properties"]
    assert "to" in generated.input_schema["properties"]
    assert "message" in generated.input_schema["properties"]
    assert "get_provider_credentials(\"twilio\")" in generated.python_code
    assert "\"From\": from_number" in generated.python_code


@pytest.mark.asyncio
async def test_codegen_hides_managed_provider_secret_fields_generically():
    spec = APISpecification(provider_name="Slack", auth={"type": "bearer", "token_header": "Authorization"})

    generated = await run_codegen(spec, "Send Slack Message V3", ManagedProviderLLM())

    assert generated.status == "pending_credentials"
    assert "channel" in generated.input_schema["properties"]
    assert "text" in generated.input_schema["properties"]
    assert "token" not in generated.input_schema["properties"]
    assert "bot_token" not in generated.input_schema["properties"]
    assert generated.input_schema["required"] == ["channel", "text"]
