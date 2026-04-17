import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.activity import Activity
from app.models.contact import Contact
from app.models.user import User


async def list_activities(db: AsyncSession, contact_id: str) -> list[dict]:
    result = await db.execute(
        select(Activity)
        .where(Activity.contact_id == contact_id)
        .order_by(Activity.follow_date.desc())
    )
    activities = result.scalars().all()
    return await _serialize(db, activities)


async def list_by_deal(db: AsyncSession, deal_id: str) -> list[dict]:
    result = await db.execute(
        select(Activity)
        .where(Activity.deal_id == deal_id)
        .order_by(Activity.follow_date.desc())
    )
    activities = result.scalars().all()
    return await _serialize(db, activities)


async def _serialize(db: AsyncSession, activities: list[Activity]) -> list[dict]:
    user_cache: dict[str, str] = {}
    data = []
    for a in activities:
        if a.user_id not in user_cache:
            u = await db.execute(select(User.name).where(User.id == a.user_id))
            user_cache[a.user_id] = u.scalar() or ""
        data.append({
            "id": a.id,
            "contact_id": a.contact_id,
            "deal_id": a.deal_id,
            "user_id": a.user_id,
            "user_name": user_cache[a.user_id],
            "type": a.type,
            "content": a.content,
            "follow_date": a.follow_date.isoformat() if a.follow_date else None,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        })
    return data


async def create_activity(
    db: AsyncSession,
    contact_id: str,
    deal_id: str,
    user_id: str,
    activity_type: str,
    content: Optional[str],
    follow_date: Optional[datetime] = None,
) -> dict:
    now = follow_date or datetime.utcnow()

    activity = Activity(
        id=str(uuid.uuid4()),
        contact_id=contact_id,
        deal_id=deal_id,
        user_id=user_id,
        type=activity_type,
        content=content,
        follow_date=now,
    )
    db.add(activity)

    result = await db.execute(select(Contact).where(Contact.id == contact_id))
    contact = result.scalar_one_or_none()
    if contact:
        contact.last_contact = now.date() if isinstance(now, datetime) else now
        contact.updated_at = datetime.utcnow()

    await db.flush()

    return {
        "id": activity.id,
        "contact_id": activity.contact_id,
        "deal_id": activity.deal_id,
        "user_id": activity.user_id,
        "type": activity.type,
        "content": activity.content,
        "follow_date": activity.follow_date.isoformat(),
        "created_at": activity.created_at.isoformat(),
    }
