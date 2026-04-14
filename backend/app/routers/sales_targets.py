from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user, require_role
from app.models.sales_target import SalesTarget
from app.models.user import User
from app.schemas.sales_target import SalesTargetCreate, SalesTargetUpdate
from app.utils.response import ok, fail

router = APIRouter()


def _target_to_dict(t: SalesTarget, user_name: str | None = None) -> dict:
    return {
        "id": t.id,
        "user_id": t.user_id,
        "user_name": user_name,
        "year": t.year,
        "month": t.month,
        "target_amount": float(t.target_amount),
        "target_count": t.target_count,
        "created_at": t.created_at.isoformat() if t.created_at else None,
        "updated_at": t.updated_at.isoformat() if t.updated_at else None,
    }


@router.get("")
async def list_targets(
    current_user: Annotated[User, Depends(require_role("admin", "manager"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    year: int | None = Query(default=None),
    user_id: str | None = Query(default=None),
):
    query = select(SalesTarget)
    if year:
        query = query.where(SalesTarget.year == year)
    if user_id:
        query = query.where(SalesTarget.user_id == user_id)

    # Manager can only see team targets
    if current_user.role == "manager":
        team_q = await db.execute(
            select(User.id).where(
                (User.manager_id == current_user.id) | (User.id == current_user.id)
            )
        )
        team_ids = [r[0] for r in team_q.all()]
        query = query.where(SalesTarget.user_id.in_(team_ids))

    query = query.order_by(SalesTarget.year.desc(), SalesTarget.month.desc())
    result = await db.execute(query)
    targets = result.scalars().all()

    # Fetch user names
    uids = list({t.user_id for t in targets})
    user_names = {}
    if uids:
        u_q = await db.execute(select(User.id, User.name).where(User.id.in_(uids)))
        user_names = {uid: name for uid, name in u_q.all()}

    return ok(data=[_target_to_dict(t, user_names.get(t.user_id)) for t in targets])


@router.post("")
async def create_target(
    body: SalesTargetCreate,
    current_user: Annotated[User, Depends(require_role("admin", "manager"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    # Check duplicate
    existing = await db.execute(
        select(SalesTarget).where(
            SalesTarget.user_id == body.user_id,
            SalesTarget.year == body.year,
            SalesTarget.month == body.month,
        )
    )
    if existing.scalar_one_or_none():
        return fail(message="该用户该月份已有目标", code=400)

    target = SalesTarget(
        user_id=body.user_id,
        year=body.year,
        month=body.month,
        target_amount=body.target_amount,
        target_count=body.target_count,
    )
    db.add(target)
    await db.commit()
    await db.refresh(target)

    # Get user name
    u_q = await db.execute(select(User.name).where(User.id == target.user_id))
    u_name = u_q.scalar_one_or_none()
    return ok(data=_target_to_dict(target, u_name))


@router.put("/{target_id}")
async def update_target(
    target_id: str,
    body: SalesTargetUpdate,
    current_user: Annotated[User, Depends(require_role("admin", "manager"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(select(SalesTarget).where(SalesTarget.id == target_id))
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="目标不存在")

    if body.target_amount is not None:
        target.target_amount = body.target_amount
    if body.target_count is not None:
        target.target_count = body.target_count

    await db.commit()
    await db.refresh(target)

    u_q = await db.execute(select(User.name).where(User.id == target.user_id))
    u_name = u_q.scalar_one_or_none()
    return ok(data=_target_to_dict(target, u_name))


@router.delete("/{target_id}")
async def delete_target(
    target_id: str,
    current_user: Annotated[User, Depends(require_role("admin"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(select(SalesTarget).where(SalesTarget.id == target_id))
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="目标不存在")

    await db.delete(target)
    await db.commit()
    return ok(data=None)
