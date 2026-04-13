from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import require_role, get_current_user
from app.models.user import User
from app.services import dashboard_service
from app.utils.response import ok

router = APIRouter()


@router.get("/admin")
async def admin_dashboard(
    user: Annotated[User, Depends(require_role("admin"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    data = await dashboard_service.get_admin_dashboard(db)
    return ok(data=data)


@router.get("/manager")
async def manager_dashboard(
    user: Annotated[User, Depends(require_role("manager"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    data = await dashboard_service.get_manager_dashboard(db, user)
    return ok(data=data)


@router.get("/sales")
async def sales_dashboard(
    user: Annotated[User, Depends(require_role("sales"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    data = await dashboard_service.get_sales_dashboard(db, user)
    return ok(data=data)


@router.get("/leaderboard")
async def leaderboard(
    user: Annotated[User, Depends(require_role("admin"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    month: str = Query(
        default=None,
        description="YYYY-MM format, defaults to current month",
    ),
):
    if not month:
        now = datetime.utcnow()
        month = f"{now.year}-{now.month:02d}"
    data = await dashboard_service.get_leaderboard(db, month)
    return ok(data=data)


@router.get("/team-leaderboard")
async def team_leaderboard(
    user: Annotated[User, Depends(require_role("manager"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    month: str = Query(
        default=None,
        description="YYYY-MM format, defaults to current month",
    ),
):
    if not month:
        now = datetime.utcnow()
        month = f"{now.year}-{now.month:02d}"
    data = await dashboard_service.get_team_leaderboard(db, user, month)
    return ok(data=data)


@router.get("/gmv-trend")
async def gmv_trend(
    user: Annotated[User, Depends(require_role("admin", "manager"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    period: str = Query(default="month", description="month or year"),
):
    data = await dashboard_service.get_gmv_trend(db, period)
    return ok(data=data)
