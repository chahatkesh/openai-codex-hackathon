"""send_email — Send an email via Resend API."""

import httpx

from app.config import settings
from app.tools import registry


async def execute(to: str, subject: str, body: str) -> str:
    """Send an email using the Resend API."""
    if not settings.resend_api_key:
        return "ERROR: Resend API key not configured. Set RESEND_API_KEY in .env"
    if not settings.resend_from_email:
        return "ERROR: Resend sender not configured. Set RESEND_FROM_EMAIL in .env"

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {settings.resend_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "from": f"FuseKit <{settings.resend_from_email}>",
                "to": [to],
                "subject": subject,
                "text": body,
            },
        )
        resp.raise_for_status()
        data = resp.json()

    return f"Email sent successfully. ID: {data.get('id', 'unknown')}"


registry.register("send_email", execute)
