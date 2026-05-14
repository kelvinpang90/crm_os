from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.message import Message
from app.models.contact import Contact
from app.schemas.message import WhatsAppSendRequest, EmailSendRequest
from app.services import whatsapp_service, email_service
from app.services.whatsapp_service import WhatsAppSendError
from app.utils.response import ok, fail

router = APIRouter()


@router.get("")
async def list_messages(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    channel: Optional[str] = None,
    is_read: Optional[bool] = None,
    contact_id: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
):
    query = select(Message)

    # Data permission
    if current_user.role == "sales":
        query = query.where(Message.assigned_to == current_user.id)
    elif current_user.role == "manager":
        from app.services.dashboard_service import _get_team_ids
        team_ids = await _get_team_ids(db, current_user.id)
        query = query.where(Message.assigned_to.in_(team_ids))

    if channel:
        query = query.where(Message.channel == channel)
    if is_read is not None:
        query = query.where(Message.is_read == is_read)
    if contact_id:
        query = query.where(Message.contact_id == contact_id)

    # Count
    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    # Paginate
    query = query.order_by(Message.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    messages = result.scalars().all()

    # Enrich with contact name
    items = []
    for m in messages:
        d = _msg_to_dict(m)
        if m.contact_id:
            cr = await db.execute(select(Contact.name).where(Contact.id == m.contact_id))
            d["contact_name"] = cr.scalar()
        items.append(d)

    return ok(data={
        "data": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    })


@router.get("/contact/{contact_id}")
async def contact_messages(
    contact_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(Message)
        .where(Message.contact_id == contact_id)
        .order_by(Message.created_at.asc())
    )
    messages = [_msg_to_dict(m) for m in result.scalars().all()]
    return ok(data=messages)


@router.patch("/{message_id}/read")
async def mark_read(
    message_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(select(Message).where(Message.id == message_id))
    msg = result.scalar_one_or_none()
    if not msg:
        return fail(message="Message not found", code=404)
    msg.is_read = True
    await db.commit()
    return ok(data=_msg_to_dict(msg))


@router.post("/whatsapp/send")
async def send_whatsapp(
    body: WhatsAppSendRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    try:
        data = await whatsapp_service.send_message(db, body.contact_id, body.message)
    except WhatsAppSendError as exc:
        if exc.reason == "no_phone":
            return fail(message="Contact not found or has no phone number", code="NO_PHONE", status_code=400)
        return fail(message=f"WhatsApp API error: {exc.detail}", code="API_ERROR", status_code=502)
    return ok(data=data)


@router.post("/email/send")
async def send_email(
    body: EmailSendRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    data = await email_service.send_email(db, body.contact_id, body.subject, body.body)
    if not data:
        return fail(message="Contact not found or has no email", code=400)
    return ok(data=data)


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
        "contact_name": None,
    }
