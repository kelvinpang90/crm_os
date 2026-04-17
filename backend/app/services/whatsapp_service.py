"""WhatsApp Cloud API integration service.

Handles inbound webhooks and outbound message sending.
Gracefully degrades when credentials are not configured.
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


def verify_webhook(mode: str, token: str, challenge: str) -> Optional[str]:
    """Verify webhook subscription from Meta."""
    if mode == "subscribe" and token == settings.whatsapp_webhook_verify_token:
        return challenge
    return None


def validate_signature(payload: bytes, signature: str) -> bool:
    """Validate X-Hub-Signature-256 header."""
    if not settings.whatsapp_app_secret:
        return True  # Skip validation in dev
    expected = hmac.new(
        settings.whatsapp_app_secret.encode(),
        payload,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)


async def process_inbound(db: AsyncSession, payload: dict) -> None:
    """Process incoming WhatsApp webhook payload."""
    try:
        entry = payload.get("entry", [])
        for e in entry:
            changes = e.get("changes", [])
            for change in changes:
                value = change.get("value", {})
                messages = value.get("messages", [])
                for msg in messages:
                    await _handle_message(db, msg)
    except Exception:
        logger.exception("Error processing WhatsApp webhook")


async def _handle_message(db: AsyncSession, msg: dict) -> None:
    phone = msg.get("from", "")
    text = ""
    if msg.get("type") == "text":
        text = msg.get("text", {}).get("body", "")
    external_id = msg.get("id")

    if not phone or not text:
        return

    # Dedup
    if external_id:
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
        # Auto-assign via routing
        assigned = await routing_service.assign_contact(db, contact)
        if assigned:
            contact.assigned_to = assigned
            await db.flush()
        # Create initial deal
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

    # Save message
    message = Message(
        id=str(uuid.uuid4()),
        contact_id=contact.id,
        channel="whatsapp",
        direction="inbound",
        sender_id=phone,
        recipient_id=settings.whatsapp_phone_number_id,
        body=text,
        external_id=external_id,
        assigned_to=contact.assigned_to,
    )
    db.add(message)
    await db.commit()


async def send_message(db: AsyncSession, contact_id: str, text: str) -> Optional[dict]:
    """Send a WhatsApp message to a contact."""
    result = await db.execute(
        select(Contact).where(Contact.id == contact_id, Contact.deleted_at.is_(None))
    )
    contact = result.scalar_one_or_none()
    if not contact or not contact.phone:
        return None

    external_id = None
    # Send via Graph API if configured
    if settings.whatsapp_access_token and settings.whatsapp_phone_number_id:
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
                if resp.status_code == 200:
                    data = resp.json()
                    external_id = data.get("messages", [{}])[0].get("id")
        except Exception:
            logger.exception("Failed to send WhatsApp message")

    # Save outbound message
    msg = Message(
        id=str(uuid.uuid4()),
        contact_id=contact_id,
        channel="whatsapp",
        direction="outbound",
        sender_id=settings.whatsapp_phone_number_id,
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
        "created_at": m.created_at.isoformat() if m.created_at else None,
    }
