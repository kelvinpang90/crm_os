from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.contact import Contact
from app.utils.response import ok

router = APIRouter()

STAGES = ["潜在客户", "跟进中", "谈判中", "已成交", "已流失"]


@router.get("")
async def get_pipeline(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    # Scope by role
    base_where = [Contact.deleted_at.is_(None)]

    if current_user.role == "sales":
        base_where.append(Contact.assigned_to == current_user.id)
    elif current_user.role == "manager":
        team_q = select(User.id).where(User.manager_id == current_user.id)
        team_result = await db.execute(team_q)
        team_ids = [r for r in team_result.scalars().all()]
        team_ids.append(current_user.id)
        base_where.append(Contact.assigned_to.in_(team_ids))

    stages = []
    for status in STAGES:
        # Count + sum
        r = await db.execute(
            select(
                func.count(Contact.id),
                func.coalesce(func.sum(Contact.deal_value), 0),
            ).where(*base_where, Contact.status == status)
        )
        count, total_value = r.one()

        # Contacts
        r = await db.execute(
            select(Contact)
            .where(*base_where, Contact.status == status)
            .order_by(Contact.deal_value.desc())
            .limit(100)
        )
        contacts = [
            {
                "id": c.id,
                "name": c.name,
                "company": c.company,
                "industry": c.industry,
                "deal_value": float(c.deal_value),
                "priority": c.priority,
                "status": c.status,
                "updated_at": c.updated_at.isoformat() if c.updated_at else None,
            }
            for c in r.scalars().all()
        ]

        stages.append({
            "status": status,
            "count": count,
            "total_value": float(total_value),
            "contacts": contacts,
        })

    return ok(data={"stages": stages})
