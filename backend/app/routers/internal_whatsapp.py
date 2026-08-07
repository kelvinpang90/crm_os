import hmac
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.services import whatsapp_service

router = APIRouter()


def _verify_internal_secret(x_internal_secret: Annotated[str | None, Header()] = None) -> None:
    if not settings.internal_shared_secret or not x_internal_secret or not hmac.compare_digest(
        x_internal_secret, settings.internal_shared_secret
    ):
        raise HTTPException(status_code=403, detail="Invalid internal secret")


@router.post("/inbound", dependencies=[Depends(_verify_internal_secret)])
async def whatsapp_inbound(
    body: dict,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Receive a message forwarded by whatsapp_gateway for the CRM demo."""
    messages = await whatsapp_service.handle_demo_inbound(db, body.get("message", {}))
    return {"messages": messages}
