from __future__ import annotations

import pytest

from app.api.credentials import get_provider_credential_detail, list_provider_credentials, upsert_provider_credentials
from app.services.provider_credentials import list_provider_credential_statuses
from app.models import ToolDefinition
from tests.helpers import DummyResult, FakeSession


@pytest.mark.asyncio
async def test_list_provider_credentials_returns_statuses(monkeypatch):
    async def fake_list():
        return [
            {
                "provider": "twilio",
                "display_name": "twilio",
                "requirements": [{"key": "TWILIO_ACCOUNT_SID", "label": "Twilio Account SID"}],
                "configured_keys": [],
                "is_configured": False,
                "affected_tools": [{"name": "send_sms", "status": "pending_credentials"}],
            }
        ]

    monkeypatch.setattr("app.api.credentials.list_provider_credential_statuses", fake_list)

    payload = await list_provider_credentials()

    assert payload[0]["provider"] == "twilio"


@pytest.mark.asyncio
async def test_get_provider_credential_detail_reports_configuration(monkeypatch):
    monkeypatch.setattr(
        "app.api.credentials.get_provider_requirements",
        lambda _provider: [{"key": "TWILIO_ACCOUNT_SID", "label": "Twilio Account SID"}],
    )

    async def fake_get(_provider: str):
        return {"TWILIO_ACCOUNT_SID": "configured"}

    async def fake_status(_provider: str):
        return {
            "provider": "twilio",
            "display_name": "twilio",
            "requirements": [{"key": "TWILIO_ACCOUNT_SID", "label": "Twilio Account SID"}],
            "configured_keys": ["TWILIO_ACCOUNT_SID"],
            "is_configured": True,
            "affected_tools": [{"name": "send_twilio_sms_v2", "status": "pending_credentials"}],
        }

    monkeypatch.setattr("app.api.credentials.get_provider_credentials", fake_get)
    monkeypatch.setattr("app.api.credentials.get_provider_credential_status", fake_status)

    payload = await get_provider_credential_detail("twilio")

    assert payload["is_configured"] is True
    assert payload["configured_keys"] == ["TWILIO_ACCOUNT_SID"]
    assert payload["affected_tools"][0]["name"] == "send_twilio_sms_v2"


@pytest.mark.asyncio
async def test_upsert_provider_credentials_persists_and_returns_detail(monkeypatch):
    monkeypatch.setattr(
        "app.api.credentials.get_provider_requirements",
        lambda _provider: [{"key": "TWILIO_ACCOUNT_SID", "label": "Twilio Account SID"}],
    )

    captured = {}

    async def fake_set(provider: str, values: dict[str, str]):
        captured["provider"] = provider
        captured["values"] = values

    async def fake_get(_provider: str):
        return {"TWILIO_ACCOUNT_SID": "configured"}

    async def fake_status(_provider: str):
        return {
            "provider": "twilio",
            "display_name": "twilio",
            "requirements": [{"key": "TWILIO_ACCOUNT_SID", "label": "Twilio Account SID"}],
            "configured_keys": ["TWILIO_ACCOUNT_SID"],
            "is_configured": True,
            "affected_tools": [{"name": "send_twilio_sms_v2", "status": "live"}],
        }

    monkeypatch.setattr("app.api.credentials.set_provider_credentials", fake_set)
    monkeypatch.setattr("app.api.credentials.get_provider_credentials", fake_get)
    monkeypatch.setattr("app.api.credentials.get_provider_credential_status", fake_status)

    payload = await upsert_provider_credentials(
        "twilio",
        request=type("Req", (), {"values": {"TWILIO_ACCOUNT_SID": "AC123"}})(),
    )

    assert captured["provider"] == "twilio"
    assert payload["is_configured"] is True
    assert payload["affected_tools"][0]["status"] == "live"


@pytest.mark.asyncio
async def test_list_provider_credential_statuses_is_dynamic(monkeypatch):
    session = FakeSession(
        execute_results=[
            DummyResult(
                [
                    ToolDefinition(
                        name="send_slack_message_v2",
                        description="Send Slack messages",
                        provider="slack",
                        cost_per_call=10,
                        status="pending_credentials",
                        input_schema={"type": "object"},
                        output_schema={"type": "object"},
                        category="communication",
                        source="pipeline",
                        version=1,
                        implementation_module="send_slack_message_v2_module",
                    )
                ]
            ),
            DummyResult([]),
        ]
    )

    class _SessionCM:
        async def __aenter__(self):
            return session

        async def __aexit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr("app.services.provider_credentials.async_session", lambda: _SessionCM())

    payload = await list_provider_credential_statuses()

    assert [item["provider"] for item in payload] == ["slack"]
