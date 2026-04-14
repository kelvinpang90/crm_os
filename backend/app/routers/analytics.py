from typing import Annotated
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, case, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.contact import Contact
from app.models.message import Message
from app.utils.response import ok

router = APIRouter()


async def _get_scoped_contact_query(current_user: User, db: AsyncSession):
    """根据角色返回可见客户的基础查询条件"""
    conditions = [Contact.deleted_at.is_(None)]
    if current_user.role == "sales":
        conditions.append(Contact.assigned_to == current_user.id)
    elif current_user.role == "manager":
        result = await db.execute(
            select(User.id).where(
                (User.manager_id == current_user.id) | (User.id == current_user.id)
            )
        )
        team_ids = [r[0] for r in result.all()]
        conditions.append(Contact.assigned_to.in_(team_ids))
    return conditions


@router.get("")
async def get_analytics(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    days: int = Query(default=90, ge=7, le=365),
):
    scope = await _get_scoped_contact_query(current_user, db)
    since = datetime.utcnow() - timedelta(days=days)

    # Overview
    overview_q = await db.execute(
        select(
            func.count(Contact.id).label("total"),
            func.sum(case((Contact.status == "已成交", 1), else_=0)).label("won"),
            func.sum(case((Contact.status == "已流失", 1), else_=0)).label("lost"),
            func.coalesce(func.sum(
                case((Contact.status == "已成交", Contact.deal_value), else_=0)
            ), 0).label("deal_amount"),
        ).where(*scope)
    )
    row = overview_q.one()
    total = row.total or 0
    won = row.won or 0
    lost = row.lost or 0
    deal_amount = float(row.deal_amount or 0)

    overview = {
        "total_contacts": total,
        "total_won": won,
        "total_lost": lost,
        "overall_conversion_rate": round(won / total * 100, 1) if total > 0 else 0,
        "total_deal_amount": deal_amount,
        "avg_deal_value": round(deal_amount / won, 2) if won > 0 else 0,
    }

    # Conversion trend (group by week)
    trend_q = await db.execute(
        select(
            func.date_format(Contact.created_at, "%Y-%m-%d").label("dt"),
            func.count(Contact.id).label("total"),
            func.sum(case((Contact.status == "已成交", 1), else_=0)).label("won"),
        )
        .where(*scope, Contact.created_at >= since)
        .group_by("dt")
        .order_by("dt")
    )
    conversion_trend = []
    for r in trend_q.all():
        t = r.total or 0
        w = r.won or 0
        conversion_trend.append({
            "date": r.dt,
            "total": t,
            "won": w,
            "rate": round(w / t * 100, 1) if t > 0 else 0,
        })

    # Channel distribution (messages)
    channel_q = await db.execute(
        select(
            Message.channel,
            func.count(Message.id).label("cnt"),
        )
        .where(Message.created_at >= since)
        .group_by(Message.channel)
    )
    channels_raw = channel_q.all()
    ch_total = sum(r.cnt for r in channels_raw) or 1
    channel_distribution = [
        {
            "channel": r.channel,
            "count": r.cnt,
            "percentage": round(r.cnt / ch_total * 100, 1),
        }
        for r in channels_raw
    ]

    # Sales ranking
    ranking_q = await db.execute(
        select(
            Contact.assigned_to,
            func.count(Contact.id).label("total_count"),
            func.sum(case((Contact.status == "已成交", 1), else_=0)).label("won_count"),
            func.coalesce(func.sum(
                case((Contact.status == "已成交", Contact.deal_value), else_=0)
            ), 0).label("deal_amount"),
        )
        .where(*scope, Contact.assigned_to.isnot(None))
        .group_by(Contact.assigned_to)
        .order_by(func.sum(case((Contact.status == "已成交", Contact.deal_value), else_=0)).desc())
    )
    rankings_raw = ranking_q.all()

    # Fetch user names
    user_ids = [r.assigned_to for r in rankings_raw if r.assigned_to]
    user_names = {}
    if user_ids:
        u_q = await db.execute(select(User.id, User.name).where(User.id.in_(user_ids)))
        user_names = {uid: name for uid, name in u_q.all()}

    sales_ranking = []
    for r in rankings_raw:
        tc = r.total_count or 0
        wc = r.won_count or 0
        sales_ranking.append({
            "user_id": r.assigned_to,
            "user_name": user_names.get(r.assigned_to, ""),
            "deal_count": wc,
            "deal_amount": float(r.deal_amount or 0),
            "conversion_rate": round(wc / tc * 100, 1) if tc > 0 else 0,
        })

    return ok(data={
        "overview": overview,
        "conversion_trend": conversion_trend,
        "channel_distribution": channel_distribution,
        "sales_ranking": sales_ranking,
    })
