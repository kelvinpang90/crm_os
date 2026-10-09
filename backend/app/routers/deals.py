from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.activity import ActivityCreate
from app.schemas.deal import DealCreate, DealUpdate
from app.services import access_service, activity_service, deal_service
from app.utils.response import fail, ok

router = APIRouter()


def _not_found(what: str = "Deal"):
    # Also the answer for a record that is not yours, so an id's existence is
    # never confirmed to someone who may not see it.
    return fail(f"{what} not found", code="NOT_FOUND", status_code=404)


def _forbidden_assignee():
    return fail("Permission denied", code="FORBIDDEN", status_code=403)


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
    if not await access_service.may_access_contact(db, current_user, body.contact_id):
        return _not_found("Contact")
    if body.assigned_to and not await access_service.may_assign_to(
        db, current_user, body.assigned_to
    ):
        return _forbidden_assignee()
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
    if not await access_service.may_access_deal(db, current_user, deal_id):
        return _not_found()
    data = {k: v for k, v in body.model_dump().items() if v is not None}
    if data.get("assigned_to") and not await access_service.may_assign_to(
        db, current_user, data["assigned_to"]
    ):
        return _forbidden_assignee()
    deal = await deal_service.update_deal(db, deal_id, data, current_user.id)
    if not deal:
        return _not_found()
    await db.commit()
    return ok(data=deal, message="Updated successfully")


@router.delete("/{deal_id}")
async def delete_deal(
    deal_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    if not await access_service.may_access_deal(db, current_user, deal_id):
        return _not_found()
    deleted = await deal_service.delete_deal(db, deal_id)
    if not deleted:
        return _not_found()
    await db.commit()
    return ok(message="Deleted successfully")


# --- Activity routes ---


@router.get("/{deal_id}/activities")
async def list_deal_activities(
    deal_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    if not await access_service.may_access_deal(db, current_user, deal_id):
        return _not_found()
    activities = await activity_service.list_by_deal(db, deal_id)
    return ok(data=activities)


@router.post("/{deal_id}/activities")
async def create_deal_activity(
    deal_id: str,
    body: ActivityCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    if not await access_service.may_access_deal(db, current_user, deal_id):
        return _not_found()
    deal = await deal_service.get_deal(db, deal_id)
    if not deal:
        return _not_found()
    activity = await activity_service.create_activity(
        db,
        deal["contact_id"],
        deal_id,
        current_user.id,
        body.type,
        body.content,
        body.follow_date,
    )
    await db.commit()
    return ok(data=activity, message="Follow-up activity recorded", status_code=201)
