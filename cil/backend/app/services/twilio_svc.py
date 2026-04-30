"""Twilio service — WhatsApp message delivery.

Credentials are optional; if absent the send is skipped and a warning is logged.
"""

import logging

from app.config import Settings

logger = logging.getLogger(__name__)


def send_whatsapp_message(to: str, body: str, settings: Settings | None = None) -> bool:
    """Send a WhatsApp message via Twilio. Returns True on success."""
    cfg = settings or Settings()

    if not cfg.twilio_account_sid or not cfg.twilio_auth_token:
        logger.warning("Twilio credentials not configured — message not sent to %s", to)
        return False

    try:
        from twilio.rest import Client  # imported lazily so missing creds don't crash

        client = Client(cfg.twilio_account_sid, cfg.twilio_auth_token)
        client.messages.create(
            body=body,
            from_=cfg.twilio_whatsapp_from,
            to=to,
        )
        logger.info("WhatsApp message sent to %s", to)
        return True
    except Exception as exc:
        logger.error("Failed to send WhatsApp message to %s: %s", to, exc)
        return False
