"""Routes with no owner to check are limited by role instead.

AutoCount sync rewrites customer data and spends API calls; the projects
reseed wipes both project tables. Both were open to any logged-in user. A
manager could also set targets for people outside their team.
"""
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import func, select

from app.models.project import Project
from app.models.sales_target import SalesTarget

from tests._people import ADMIN, BOSS, REP, logged_in_as, seed_people


@pytest.mark.parametrize("user, allowed", [(REP, False), (BOSS, True), (ADMIN, True)])
async def test_autocount_sync_needs_admin_or_manager(client, async_session_maker, user, allowed):
    await seed_people(async_session_maker)
    with patch(
        "app.services.autocount_service.sync_all", new=AsyncMock(return_value={})
    ) as mock_sync, logged_in_as(user):
        resp = await client.post("/api/autocount/sync")
    assert (resp.status_code == 200) is allowed
    assert mock_sync.await_count == (1 if allowed else 0)


@pytest.mark.parametrize("user", [REP, BOSS])
async def test_projects_reseed_is_admin_only(client, async_session_maker, user):
    await seed_people(async_session_maker)
    async with async_session_maker() as session:
        session.add(Project(id="p-real", customer_name="Kept"))
        await session.commit()
    with logged_in_as(user):
        resp = await client.post("/api/projects/seed-demo")
    assert resp.status_code == 403
    async with async_session_maker() as session:
        kept = (
            await session.execute(select(func.count()).select_from(Project).where(Project.id == "p-real"))
        ).scalar()
    assert kept == 1


async def _seed_targets(session_maker) -> None:
    await seed_people(session_maker)
    async with session_maker() as session:
        session.add_all([
            SalesTarget(id="st-rep", user_id="u-rep", year=2026, month=10, target_amount=1),
            SalesTarget(id="st-other", user_id="u-other", year=2026, month=10, target_amount=1),
        ])
        await session.commit()


async def test_manager_sets_targets_for_own_team_only(client, async_session_maker):
    await _seed_targets(async_session_maker)
    body = {"year": 2026, "month": 11, "target_amount": 5}
    with logged_in_as(BOSS):
        inside = await client.post("/api/sales-targets", json={**body, "user_id": "u-rep"})
        outside = await client.post("/api/sales-targets", json={**body, "user_id": "u-other"})
    assert inside.status_code == 200
    assert outside.status_code == 403


async def test_manager_edits_targets_for_own_team_only(client, async_session_maker):
    await _seed_targets(async_session_maker)
    with logged_in_as(BOSS):
        inside = await client.put("/api/sales-targets/st-rep", json={"target_amount": 9})
        outside = await client.put("/api/sales-targets/st-other", json={"target_amount": 9})
    assert inside.status_code == 200
    assert outside.status_code == 404
