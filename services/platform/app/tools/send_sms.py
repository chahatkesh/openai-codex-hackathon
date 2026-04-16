"""send_sms — Send an SMS via Twilio."""

import httpx
from base64 import b64encode

from app.config import settings
from app.tools import registry


async def execute(to: str, message: str) -> str:
    """Send an SMS using Twilio."""
    if not settings.twilio_account_sid or not settings.twilio_auth_token:
        return "ERROR: Twilio credentials not configured. Set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER in .env"

    url = f"https://api.twilio.com/2010-04-01/Accounts/{settings.twilio_account_sid}/Messages.json"
    auth_str = b64encode(f"{settings.twilio_account_sid}:{settings.twilio_auth_token}".encode()).decode()

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            url,
            headers={"Authorization": f"Basic {auth_str}"},
            data={
                "To": to,
                "From": settings.twilio_from_number,
                "Body": message,
            },
        )
        resp.raise_for_status()
        data = resp.json()

    return f"SMS sent successfully. SID: {data.get('sid', 'unknown')}"


registry.register("send_sms", execute)
