"""Twilio service wrapper.

All WhatsApp messaging goes through send_whatsapp() — never import
the Twilio client directly in route or agent files.
"""

import asyncio
import logging

from twilio.rest import Client

from app.config import Settings

logger = logging.getLogger("cil.twilio")


def _get_client(settings: Settings) -> Client:
    return Client(settings.twilio_account_sid, settings.twilio_auth_token)


async def send_whatsapp(
    to: str,
    body: str,
    settings: Settings,
) -> str:
    """Send a WhatsApp message via the Twilio sandbox.

    Args:
        to: Recipient phone number. Accepts "+2348012345678" or
            "whatsapp:+2348012345678" — the prefix is added if missing.
        body: Message text to send.
        settings: Injected application settings.

    Returns:
        Twilio message SID.
    """
    if not to.startswith("whatsapp:"):
        to = f"whatsapp:{to}"

    client = _get_client(settings)
    message = await asyncio.to_thread(
        lambda: client.messages.create(
            from_=settings.twilio_whatsapp_from,
            to=to,
            body=body,
        )
    )
    logger.info("WhatsApp sent sid=%s to=%s", message.sid, to)
    return message.sid
