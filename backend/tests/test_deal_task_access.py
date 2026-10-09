"""Deals and tasks opened by id need the ownership their lists already apply.

Deals are judged by their own owner (as the deal list and pipeline are) and
tasks by theirs. A refusal answers exactly like a missing record: 404
NOT_FOUND. Tasks used to answer "not found" with HTTP 400; they now say 404.
"""

import pytest
from sqlalchemy import select

from app.models.contact import Contact
from app.models.deal import Deal
from app.models.task import Task
from tests._people import ADMIN, BOSS, OTHER, REP, logged_in_as, seed_people


async def _seed(session_maker) -> None:
    await seed_people(session_maker)
    async with session_maker() as session:
        session.add_all(
            [
                Deal(id="d-mine", contact_id="c-mine", assigned_to="u-rep"),
                Deal(id="d-theirs", contact_id="c-theirs", assigned_to="u-other"),
                Task(id="t-mine", title="Call back", contact_id="c-mine", assigned_to="u-rep"),
            ]
        )
        await session.commit()


REP_DEAL_ROUTES = [
    ("put", "/api/deals/d-mine", {"amount": "999"}),
    ("delete", "/api/deals/d-mine", None),
    ("get", "/api/deals/d-mine/activities", None),
    ("post", "/api/deals/d-mine/activities", {"deal_id": "d-mine", "type": "phone"}),
]

REP_TASK_ROUTES = [
    ("get", "/api/tasks/t-mine", None),
    ("put", "/api/tasks/t-mine", {"title": "Hijacked"}),
    ("patch", "/api/tasks/t-mine/toggle", None),
    ("delete", "/api/tasks/t-mine", None),
]


async def _call(client, method, url, body):
    kwargs = {"json": body} if body is not None else {}
    return await getattr(client, method)(url, **kwargs)


@pytest.mark.parametrize("method, url, body", REP_DEAL_ROUTES + REP_TASK_ROUTES)
async def test_stranger_gets_not_found(client, async_session_maker, method, url, body):
    await _seed(async_session_maker)
    with logged_in_as(OTHER):
        resp = await _call(client, method, url, body)
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "NOT_FOUND"


@pytest.mark.parametrize("method, url, body", REP_DEAL_ROUTES + REP_TASK_ROUTES)
@pytest.mark.parametrize("user", [REP, BOSS, ADMIN])
async def test_owner_team_and_admin_get_through(
    client, async_session_maker, user, method, url, body
):
    await _seed(async_session_maker)
    with logged_in_as(user):
        resp = await _call(client, method, url, body)
    assert resp.status_code in (200, 201)


@pytest.mark.parametrize("url", ["/api/tasks/t-nope", "/api/deals/d-nope/activities"])
async def test_missing_reads_like_foreign(client, async_session_maker, url):
    await _seed(async_session_maker)
    foreign_url = url.replace("t-nope", "t-mine").replace("d-nope", "d-mine")
    with logged_in_as(OTHER):
        missing = await client.get(url)
        foreign = await client.get(foreign_url)
    assert missing.status_code == foreign.status_code == 404
    assert missing.json() == foreign.json()


async def test_rep_cannot_take_a_deal(client, async_session_maker):
    await _seed(async_session_maker)
    with logged_in_as(REP):
        resp = await client.put("/api/deals/d-mine", json={"assigned_to": "u-other"})
    assert resp.status_code == 403


async def test_rep_cannot_open_a_deal_on_someone_elses_customer(client, async_session_maker):
    await _seed(async_session_maker)
    with logged_in_as(REP):
        resp = await client.post(
            "/api/deals", json={"contact_id": "c-theirs", "assigned_to": "u-rep"}
        )
    assert resp.status_code == 404


async def test_rep_cannot_file_a_task_against_someone_elses_customer(client, async_session_maker):
    await _seed(async_session_maker)
    with logged_in_as(REP):
        created = await client.post("/api/tasks", json={"title": "Peek", "contact_id": "c-theirs"})
        moved = await client.put("/api/tasks/t-mine", json={"contact_id": "c-theirs"})
    assert created.status_code == 404
    assert moved.status_code == 404
    async with async_session_maker() as session:
        contact_id = (
            await session.execute(select(Task.contact_id).where(Task.id == "t-mine"))
        ).scalar_one()
    assert contact_id == "c-mine"


async def test_rep_edits_task_that_points_at_a_customer_beyond_reach(client, async_session_maker):
    """A manager may give a rep a task about the manager's own customer. The
    edit form sends the unchanged link back, and that must not lock the rep out
    of their own task -- only a link being changed is checked."""
    await _seed(async_session_maker)
    async with async_session_maker() as session:
        session.add_all(
            [
                Contact(id="c-boss", name="Boss's", phone="60155555555", assigned_to="u-boss"),
                Task(id="t-handed", title="Visit", contact_id="c-boss", assigned_to="u-rep"),
            ]
        )
        await session.commit()
    with logged_in_as(REP):
        resp = await client.put(
            "/api/tasks/t-handed",
            json={"title": "Visit Tuesday", "contact_id": "c-boss", "assigned_to": "u-rep"},
        )
    assert resp.status_code == 200


async def test_rep_cannot_assign_a_task_to_someone_else(client, async_session_maker):
    await _seed(async_session_maker)
    with logged_in_as(REP):
        resp = await client.post("/api/tasks", json={"title": "Yours", "assigned_to": "u-other"})
    assert resp.status_code == 403


async def test_manager_assigns_tasks_within_team(client, async_session_maker):
    await _seed(async_session_maker)
    with logged_in_as(BOSS):
        inside = await client.post("/api/tasks", json={"title": "Team", "assigned_to": "u-rep"})
        outside = await client.post(
            "/api/tasks", json={"title": "Not team", "assigned_to": "u-other"}
        )
    assert inside.status_code == 200
    assert outside.status_code == 403


async def test_admin_missing_task_is_a_real_404(client, async_session_maker):
    await _seed(async_session_maker)
    with logged_in_as(ADMIN):
        resp = await client.get("/api/tasks/t-nope")
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "NOT_FOUND"
