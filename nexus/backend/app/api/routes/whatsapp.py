"""WhatsApp webhook endpoint (Twilio sandbox).

POST /api/v1/whatsapp/webhook — receives inbound WhatsApp messages from
Twilio and returns a TwiML XML response with the agent's reply.

All Phase 1 WhatsApp messages are handled by the Fan Agent (SONA).
Always returns HTTP 200 so Twilio does not retry the webhook.
"""

import logging

from fastapi import APIRouter, Form, Response

from app.dependencies import get_graph

logger = logging.getLogger("nexus.api.whatsapp")

router = APIRouter()

_TWIML = '<?xml version="1.0" encoding="UTF-8"?><Response><Message>{body}</Message></Response>'


@router.post("/whatsapp/webhook")
async def whatsapp_webhook(
    Body: str = Form(default=""),
    From: str = Form(default=""),
    WaId: str = Form(default=""),
) -> Response:
    """Handle an inbound WhatsApp message and reply via TwiML."""
    session_id = WaId or From.replace("whatsapp:", "").replace("+", "")
    logger.info("WhatsApp inbound from=%s session=%s", From, session_id)

    graph = get_graph()

    state = {
        "message": Body,
        "channel": "whatsapp",
        "session_id": session_id,
        "target_agent": "fan",
        "conversation_history": [],
        "retrieved_docs": [],
        "agent_response": "",
        "sources": [],
        "error": None,
    }

    try:
        result = await graph.ainvoke(state)
        reply = result.get("agent_response") or "Sorry, I couldn't process that. Please try again!"
    except Exception as exc:
        logger.exception("Orchestrator error for WhatsApp session %s", session_id)
        reply = "Something went wrong on our end. Please try again in a moment!"

    twiml = _TWIML.format(body=reply)
    return Response(content=twiml, media_type="application/xml")
