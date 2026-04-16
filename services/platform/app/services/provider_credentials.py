from __future__ import annotations

from typing import Any

from sqlalchemy import select

from app.db import async_session
from app.models import ProviderCredential, ToolDefinition

PROVIDER_REQUIREMENTS: dict[str, list[dict[str, str]]] = {
    "twilio": [
        {"key": "TWILIO_ACCOUNT_SID", "label": "Twilio Account SID"},
        {"key": "TWILIO_AUTH_TOKEN", "label": "Twilio Auth Token"},
        {"key": "TWILIO_FROM_NUMBER", "label": "Twilio From Number"},
    ],
    "slack": [
        {"key": "SLACK_BOT_TOKEN", "label": "Slack Bot Token"},
    ],
    "resend": [
        {"key": "RESEND_API_KEY", "label": "Resend API Key"},
    ],
}


def normalize_provider(provider: str) -> str:
    return provider.strip().lower().replace(" ", "_")


def get_provider_requirements(provider: str) -> list[dict[str, str]]:
    return PROVIDER_REQUIREMENTS.get(normalize_provider(provider), [])


async def get_provider_credentials(provider: str) -> dict[str, str]:
    normalized = normalize_provider(provider)
    async with async_session() as session:
        result = await session.execute(
            select(ProviderCredential).where(
                ProviderCredential.provider == normalized,
                ProviderCredential.is_active.is_(True),
            )
        )
        rows = result.scalars().all()
        return {row.key: row.value for row in rows}


async def set_provider_credentials(provider: str, values: dict[str, str]) -> None:
    normalized = normalize_provider(provider)
    async with async_session() as session:
        result = await session.execute(
            select(ProviderCredential).where(ProviderCredential.provider == normalized)
        )
        existing = {row.key: row for row in result.scalars().all()}

        for key, value in values.items():
            if key in existing:
                existing[key].value = value
                existing[key].is_active = True
            else:
                session.add(
                    ProviderCredential(
                        provider=normalized,
                        key=key,
                        value=value,
                        is_active=True,
                    )
                )

        tool_result = await session.execute(select(ToolDefinition))
        requirements = get_provider_requirements(normalized)
        required_keys = {item["key"] for item in requirements}
        combined_keys = set(values) | {
            row.key for row in existing.values() if row.is_active
        }
        is_complete = not required_keys or required_keys.issubset(combined_keys)

        for tool in tool_result.scalars().all():
            if (
                normalize_provider(tool.provider) == normalized
                and tool.status == "pending_credentials"
                and is_complete
            ):
                tool.status = "live"

        await session.commit()


async def list_provider_credential_statuses() -> list[dict[str, Any]]:
    async with async_session() as session:
        tools_result = await session.execute(select(ToolDefinition))
        tools = tools_result.scalars().all()

        creds_result = await session.execute(
            select(ProviderCredential).where(ProviderCredential.is_active.is_(True))
        )
        stored_rows = creds_result.scalars().all()
        stored_by_provider: dict[str, set[str]] = {}
        for row in stored_rows:
            stored_by_provider.setdefault(row.provider, set()).add(row.key)

        providers = {normalize_provider(tool.provider): tool.provider for tool in tools}
        for provider in stored_by_provider:
            providers.setdefault(provider, provider)

        payload: list[dict[str, Any]] = []
        for normalized, display_name in sorted(providers.items()):
            requirements = get_provider_requirements(normalized)
            required_keys = {item["key"] for item in requirements}
            stored_keys = stored_by_provider.get(normalized, set())
            affected_tools = [
                {
                    "name": tool.name,
                    "status": tool.status,
                }
                for tool in tools
                if normalize_provider(tool.provider) == normalized
            ]
            payload.append(
                {
                    "provider": normalized,
                    "display_name": display_name,
                    "requirements": requirements,
                    "configured_keys": sorted(stored_keys),
                    "is_configured": bool(required_keys) and required_keys.issubset(stored_keys),
                    "affected_tools": affected_tools,
                }
            )
        return payload


async def get_provider_credential_status(provider: str) -> dict[str, Any]:
    normalized = normalize_provider(provider)
    all_statuses = await list_provider_credential_statuses()
    for status in all_statuses:
        if status["provider"] == normalized:
            return status

    requirements = get_provider_requirements(normalized)
    return {
        "provider": normalized,
        "display_name": provider,
        "requirements": requirements,
        "configured_keys": [],
        "is_configured": False,
        "affected_tools": [],
    }
