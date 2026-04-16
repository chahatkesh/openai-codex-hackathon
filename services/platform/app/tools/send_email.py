"""send_email — Send an email via Resend API."""

import httpx

from app.config import settings
from app.services.provider_credentials import get_provider_credentials
from app.tools import registry


async def execute(to: str, subject: str, body: str) -> str:
    """Send an email using the Resend API."""
    creds = await get_provider_credentials("resend")
    resend_api_key = creds.get("RESEND_API_KEY") or settings.resend_api_key
    resend_from_email = creds.get("RESEND_FROM_EMAIL") or settings.resend_from_email

    if not resend_api_key:
        return "ERROR: Resend API key not configured. Set RESEND_API_KEY in .env"
    if not resend_from_email:
        return "ERROR: Resend sender not configured. Set RESEND_FROM_EMAIL in .env"

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {resend_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "from": f"FuseKit <{resend_from_email}>",
                "to": [to],
                "subject": subject,
                "text": body,
            },
        )
        resp.raise_for_status()
        data = resp.json()

    return f"Email sent successfully. ID: {data.get('id', 'unknown')}"


registry.register("send_email", execute)
