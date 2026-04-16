"""send_sms — Send an SMS via Twilio."""

import httpx
from base64 import b64encode

from app.config import settings
from app.services.provider_credentials import get_provider_credentials
from app.tools import registry


async def execute(to: str, message: str) -> str:
    """Send an SMS using Twilio."""
    creds = await get_provider_credentials("twilio")
    account_sid = creds.get("TWILIO_ACCOUNT_SID") or settings.twilio_account_sid
    auth_token = creds.get("TWILIO_AUTH_TOKEN") or settings.twilio_auth_token
    from_number = creds.get("TWILIO_FROM_NUMBER") or settings.twilio_from_number

    if not account_sid or not auth_token or not from_number:
        return "ERROR: Twilio credentials not configured. Set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER in .env"

    url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"
    auth_str = b64encode(f"{account_sid}:{auth_token}".encode()).decode()

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

    return f"SMS sent successfully. SID: {data.get('sid', 'unknown')}"


registry.register("send_sms", execute)
