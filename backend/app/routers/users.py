from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.utils.response import ok, fail

router = APIRouter()


def _user_to_dict(u: User) -> dict:
    return {
        "id": u.id,
        "name": u.name,
        "email": u.email,
        "role": u.role,
        "avatar_url": u.avatar_url,
        "language": u.language,
        "manager_id": u.manager_id,
        "is_active": u.is_active,
        "created_at": u.created_at.isoformat() if u.created_at else None,
    }


@router.get("")
async def list_users(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    query = select(User).where(User.is_active == True)

    if current_user.role == "sales":
        query = query.where(User.id == current_user.id)
    elif current_user.role == "manager":
        query = query.where(
            (User.manager_id == current_user.id) | (User.id == current_user.id)
        )
    # admin sees all

    result = await db.execute(query.order_by(User.name))
    users = result.scalars().all()
    return ok(data=[_user_to_dict(u) for u in users])


@router.patch("/me/language")
async def update_language(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    body: dict,
):
    language = body.get("language")
    if language not in ("zh", "en"):
        return fail(message="语言必须为 zh 或 en", code=400)

    current_user.language = language
    await db.commit()
    await db.refresh(current_user)
    return ok(data=_user_to_dict(current_user))
