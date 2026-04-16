from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.provider_credentials import (
    get_provider_credentials,
    get_provider_requirements,
    list_provider_credential_statuses,
    normalize_provider,
    set_provider_credentials,
)

router = APIRouter(prefix="/api/credentials", tags=["credentials"])


class CredentialUpsertRequest(BaseModel):
    values: dict[str, str]


@router.get("/providers")
async def list_provider_credentials():
    return await list_provider_credential_statuses()


@router.get("/{provider}")
async def get_provider_credential_detail(provider: str):
    normalized = normalize_provider(provider)
    requirements = get_provider_requirements(normalized)
    values = await get_provider_credentials(normalized)
    return {
        "provider": normalized,
        "requirements": requirements,
        "configured_keys": sorted(values.keys()),
        "is_configured": bool(requirements)
        and {item["key"] for item in requirements}.issubset(values.keys()),
    }


@router.post("/{provider}")
async def upsert_provider_credentials(provider: str, request: CredentialUpsertRequest):
    normalized = normalize_provider(provider)
    requirements = get_provider_requirements(normalized)
    if not requirements:
        raise HTTPException(status_code=400, detail=f"Provider '{provider}' is not credential-managed yet")

    sanitized: dict[str, str] = {
        key: value
        for key, value in request.values.items()
        if key in {item["key"] for item in requirements} and value.strip()
    }
    if not sanitized:
        raise HTTPException(status_code=400, detail="No valid credential values were provided")

    await set_provider_credentials(normalized, sanitized)
    return await get_provider_credential_detail(normalized)
