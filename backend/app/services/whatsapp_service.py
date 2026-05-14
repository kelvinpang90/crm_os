"""WhatsApp Cloud API integration service.

Handles inbound webhooks (messages + status callbacks) and outbound message
sending. Gracefully degrades when credentials are not configured.
"""

import hashlib
import hmac
import uuid
import logging
from typing import Optional

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.message import Message
from app.models.contact import Contact
from app.services import routing_service

logger = logging.getLogger(__name__)

GRAPH_API = "https://graph.facebook.com/v18.0"

_signature_skip_warned = False


class WhatsAppSendError(Exception):
    """Raised when sending an outbound WhatsApp message fails.

    `reason` is one of: "no_phone", "api_error".
    """

    def __init__(self, reason: str, detail: str = ""):
        super().__init__(detail or reason)
        self.reason = reason
        self.detail = detail


def verify_webhook(mode: str, token: str, challenge: str) -> Optional[str]:
    """Verify webhook subscription from Meta."""
    if mode == "subscribe" and token == settings.whatsapp_webhook_verify_token:
        return challenge
    return None


def validate_signature(payload: bytes, signature: str) -> bool:
    """Validate X-Hub-Signature-256 header."""
    global _signature_skip_warned
    if not settings.whatsapp_app_secret:
        if not _signature_skip_warned:
            logger.warning(
                "WHATSAPP_APP_SECRET not set — webhook signature validation is disabled. "
                "Do NOT run this configuration in production."
            )
            _signature_skip_warned = True
        return True
    expected = hmac.new(
        settings.whatsapp_app_secret.encode(),
        payload,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)


async def process_inbound(db: AsyncSession, payload: dict) -> None:
    """Process incoming WhatsApp webhook payload (messages + statuses)."""
    try:
        for entry in payload.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})
                for msg in value.get("messages", []):
                    await _handle_message(db, msg)
                for status in value.get("statuses", []):
                    _handle_status(status)
    except Exception:
        logger.exception("Error processing WhatsApp webhook")


def _extract_body(msg: dict) -> str:
    """Map any inbound message type to a textual body. Never returns empty."""
    mtype = msg.get("type", "unknown")

    if mtype == "text":
        return msg.get("text", {}).get("body", "") or "[empty text]"

    if mtype == "image":
        caption = msg.get("image", {}).get("caption")
        return f"[image] {caption}" if caption else "[image]"

    if mtype == "document":
        doc = msg.get("document", {})
        name = doc.get("filename") or doc.get("id", "")
        caption = doc.get("caption")
        base = f"[document: {name}]" if name else "[document]"
        return f"{base} {caption}" if caption else base

    if mtype == "audio":
        return "[audio]"

    if mtype == "video":
        caption = msg.get("video", {}).get("caption")
        return f"[video] {caption}" if caption else "[video]"

    if mtype == "sticker":
        return "[sticker]"

    if mtype == "location":
        loc = msg.get("location", {})
        return f"[location: {loc.get('latitude')},{loc.get('longitude')}]"

    if mtype == "button":
        return msg.get("button", {}).get("text") or "[button reply]"

    if mtype == "interactive":
        inter = msg.get("interactive", {})
        itype = inter.get("type")
        if itype == "button_reply":
            return inter.get("button_reply", {}).get("title") or "[button reply]"
        if itype == "list_reply":
            return inter.get("list_reply", {}).get("title") or "[list reply]"
        return f"[interactive: {itype}]"

    if mtype == "contacts":
        return "[contacts shared]"

    return f"[unsupported: {mtype}]"


async def _handle_message(db: AsyncSession, msg: dict) -> None:
    phone = msg.get("from", "")
    external_id = msg.get("id")
    if not phone or not external_id:
        logger.warning("WhatsApp inbound missing from/id: %s", msg)
        return

    body = _extract_body(msg)

    # Dedup
    existing = await db.execute(
        select(Message).where(Message.external_id == external_id)
    )
    if existing.scalar_one_or_none():
        return

    # Find or create contact
    result = await db.execute(
        select(Contact).where(
            Contact.phone == phone,
            Contact.deleted_at.is_(None),
        )
    )
    contact = result.scalar_one_or_none()

    if not contact:
        contact = Contact(
            id=str(uuid.uuid4()),
            name=phone,
            phone=phone,
        )
        db.add(contact)
        await db.flush()
        assigned = await routing_service.assign_contact(db, contact)
        if assigned:
            contact.assigned_to = assigned
            await db.flush()
        from app.models.deal import Deal
        deal = Deal(
            id=str(uuid.uuid4()),
            contact_id=contact.id,
            status="lead",
            priority="mid",
            amount=0.0,
            assigned_to=contact.assigned_to,
        )
        db.add(deal)

    message = Message(
        id=str(uuid.uuid4()),
        contact_id=contact.id,
        channel="whatsapp",
        direction="inbound",
        sender_id=phone,
        recipient_id=settings.whatsapp_phone_number_id,
        body=body,
        external_id=external_id,
        assigned_to=contact.assigned_to,
    )
    db.add(message)
    await db.commit()


def _handle_status(status: dict) -> None:
    """Log delivery/read receipts. Not persisted (no schema change in this pass)."""
    s = status.get("status")
    ext_id = status.get("id")
    recipient = status.get("recipient_id")
    if s == "failed":
        errors = status.get("errors", [])
        logger.error(
            "WhatsApp status=failed external_id=%s recipient=%s errors=%s",
            ext_id, recipient, errors,
        )
    else:
        logger.info(
            "WhatsApp status=%s external_id=%s recipient=%s",
            s, ext_id, recipient,
        )


async def send_message(db: AsyncSession, contact_id: str, text: str) -> dict:
    """Send a WhatsApp message to a contact.

    Raises WhatsAppSendError on failure. On success, returns the persisted
    message as a dict. When credentials are unset, the message is still
    persisted (dev mode) and a warning is logged.
    """
    result = await db.execute(
        select(Contact).where(Contact.id == contact_id, Contact.deleted_at.is_(None))
    )
    contact = result.scalar_one_or_none()
    if not contact or not contact.phone:
        raise WhatsAppSendError("no_phone", "Contact not found or has no phone number")

    external_id = None
    creds_configured = bool(
        settings.whatsapp_access_token and settings.whatsapp_phone_number_id
    )

    if creds_configured:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{GRAPH_API}/{settings.whatsapp_phone_number_id}/messages",
                    headers={"Authorization": f"Bearer {settings.whatsapp_access_token}"},
                    json={
                        "messaging_product": "whatsapp",
                        "to": contact.phone,
                        "type": "text",
                        "text": {"body": text},
                    },
                    timeout=10,
                )
        except httpx.HTTPError as exc:
            logger.exception("WhatsApp send transport error")
            raise WhatsAppSendError("api_error", str(exc)) from exc

        if resp.status_code != 200:
            logger.error(
                "WhatsApp send failed status=%s body=%s",
                resp.status_code, resp.text,
            )
            raise WhatsAppSendError("api_error", f"HTTP {resp.status_code}: {resp.text}")

        data = resp.json()
        external_id = data.get("messages", [{}])[0].get("id")
    else:
        logger.warning(
            "WhatsApp credentials not configured — persisting outbound message without dispatch"
        )

    msg = Message(
        id=str(uuid.uuid4()),
        contact_id=contact_id,
        channel="whatsapp",
        direction="outbound",
        sender_id=settings.whatsapp_phone_number_id or "dev",
        recipient_id=contact.phone,
        body=text,
        external_id=external_id,
        is_read=True,
        assigned_to=contact.assigned_to,
    )
    db.add(msg)
    await db.commit()
    await db.refresh(msg)
    return _msg_to_dict(msg)


def _msg_to_dict(m: Message) -> dict:
    return {
        "id": m.id,
        "contact_id": m.contact_id,
        "channel": m.channel,
        "direction": m.direction,
        "sender_id": m.sender_id,
        "recipient_id": m.recipient_id,
        "subject": m.subject,
        "body": m.body,
        "external_id": m.external_id,
        "is_read": m.is_read,
        "assigned_to": m.assigned_to,
        # Append "Z" so the frontend parses created_at as UTC instead of local time.
        # DB stores UTC (default=datetime.utcnow) but isoformat() is naive — without
        # the suffix dayjs treats it as local time and renders an 8h skew (MYT).
        "created_at": m.created_at.isoformat() + "Z" if m.created_at else None,
    }
