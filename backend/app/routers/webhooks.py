from typing import Annotated

from fastapi import APIRouter, Request, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from app.database import get_db
from app.services import whatsapp_service

router = APIRouter()


@router.get("/whatsapp")
async def whatsapp_verify(
    mode: str = Query(alias="hub.mode", default=""),
    token: str = Query(alias="hub.verify_token", default=""),
    challenge: str = Query(alias="hub.challenge", default=""),
):
    """Meta webhook verification endpoint."""
    result = whatsapp_service.verify_webhook(mode, token, challenge)
    if result:
        return Response(content=result, media_type="text/plain")
    return Response(status_code=403)


@router.post("/whatsapp")
async def whatsapp_webhook(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Receive WhatsApp webhook events from Meta."""
    body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256", "")

    if not whatsapp_service.validate_signature(body, signature):
        return Response(status_code=403)

    payload = await request.json()
    await whatsapp_service.process_inbound(db, payload)

    # Must return 200 to prevent Meta retries
    return {"status": "ok"}
