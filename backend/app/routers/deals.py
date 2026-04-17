from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.activity import ActivityCreate
from app.schemas.deal import DealCreate, DealUpdate
from app.services import deal_service, activity_service
from app.utils.response import ok, fail

router = APIRouter()


@router.get("")
async def list_deals(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    contact_id: Optional[str] = Query(None),
):
    deals = await deal_service.list_deals(db, current_user, contact_id)
    return ok(data=deals)


@router.post("")
async def create_deal(
    body: DealCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    deal = await deal_service.create_deal(db, body.contact_id, body.model_dump(), current_user.id)
    await db.commit()
    return ok(data=deal, message="Deal created", status_code=201)


@router.put("/{deal_id}")
async def update_deal(
    deal_id: str,
    body: DealUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    data = {k: v for k, v in body.model_dump().items() if v is not None}
    deal = await deal_service.update_deal(db, deal_id, data, current_user.id)
    if not deal:
        return fail("Deal not found", code="NOT_FOUND", status_code=404)
    await db.commit()
    return ok(data=deal, message="Updated successfully")


@router.delete("/{deal_id}")
async def delete_deal(
    deal_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _current_user: Annotated[User, Depends(get_current_user)],
):
    deleted = await deal_service.delete_deal(db, deal_id)
    if not deleted:
        return fail("Deal not found", code="NOT_FOUND", status_code=404)
    await db.commit()
    return ok(message="Deleted successfully")


# --- Activity routes ---

@router.get("/{deal_id}/activities")
async def list_deal_activities(
    deal_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _current_user: Annotated[User, Depends(get_current_user)],
):
    activities = await activity_service.list_by_deal(db, deal_id)
    return ok(data=activities)


@router.post("/{deal_id}/activities")
async def create_deal_activity(
    deal_id: str,
    body: ActivityCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    deal = await deal_service.get_deal(db, deal_id)
    if not deal:
        return fail("Deal not found", code="NOT_FOUND", status_code=404)
    activity = await activity_service.create_activity(
        db, deal["contact_id"], deal_id, current_user.id, body.type, body.content, body.follow_date,
    )
    await db.commit()
    return ok(data=activity, message="Follow-up activity recorded", status_code=201)
