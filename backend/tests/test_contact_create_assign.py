"""Creating a customer may hand it only to someone the creator could hand it to later.

Editing a customer already checked `may_assign_to`, but `POST /api/contacts` and
the import sheet's `assigned_to_email` column let a new customer go to anyone.
Creation now applies the same rule: the API answers exactly as an out-of-reach
edit does (403 FORBIDDEN), and the import rejects the row with the same error as
an unknown account, so the sheet cannot be used to probe which emails exist.
"""

import pytest_asyncio
from sqlalchemy import func, select

from app.database import get_db
from app.main import app
from app.models.contact import Contact
from app.services import contact_service
from tests._people import ADMIN, BOSS, OTHER, REP, logged_in_as, seed_people


@pytest_asyncio.fixture
async def committing_client(client, async_session_maker):
    """`client`, but each request commits like the real `get_db`, so a refused
    create can be told apart from one that was only rolled back."""

    async def _get_db_committing():
        async with async_session_maker() as session:
            yield session
            await session.commit()

    app.dependency_overrides[get_db] = _get_db_committing
    yield client


async def _contact_count(session_maker, name: str) -> int:
    async with session_maker() as session:
        return (
            await session.execute(
                select(func.count()).select_from(Contact).where(Contact.name == name)
            )
        ).scalar()


async def _create(client, user, assigned_to):
    body = {"name": "New Customer"}
    if assigned_to is not None:
        body["assigned_to"] = assigned_to
    with logged_in_as(user):
        return await client.post("/api/contacts", json=body)


# --- POST /api/contacts ---


async def test_rep_cannot_create_for_someone_else(committing_client, async_session_maker):
    """AC1: assigned_to outside the creator's reach -> the edit's 403, nothing created."""
    await seed_people(async_session_maker)
    resp = await _create(committing_client, REP, "u-other")
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "FORBIDDEN"
    assert await _contact_count(async_session_maker, "New Customer") == 0


async def test_refusal_matches_the_edit_refusal(committing_client, async_session_maker):
    """AC1: the create refusal is the very response an out-of-reach edit returns."""
    await seed_people(async_session_maker)
    created = await _create(committing_client, REP, "u-other")
    with logged_in_as(REP):
        edited = await committing_client.put(
            "/api/contacts/c-mine", json={"assigned_to": "u-other"}
        )
    assert created.status_code == edited.status_code == 403
    assert created.json() == edited.json()


async def test_rep_creates_for_themselves(committing_client, async_session_maker):
    """AC1: assigned_to within reach (a rep's own id) behaves as before."""
    await seed_people(async_session_maker)
    resp = await _create(committing_client, REP, "u-rep")
    assert resp.status_code == 201
    assert resp.json()["data"]["assigned_to"] == "u-rep"
    assert await _contact_count(async_session_maker, "New Customer") == 1


async def test_rep_without_assignee_still_gets_it(committing_client, async_session_maker):
    """AC1: no assigned_to behaves as before -- a rep's new customer is their own."""
    await seed_people(async_session_maker)
    resp = await _create(committing_client, REP, None)
    assert resp.status_code == 201
    assert resp.json()["data"]["assigned_to"] == "u-rep"


async def test_manager_creates_for_own_team(committing_client, async_session_maker):
    """AC1: a manager may hand a new customer to someone on their team."""
    await seed_people(async_session_maker)
    resp = await _create(committing_client, BOSS, "u-rep")
    assert resp.status_code == 201
    assert resp.json()["data"]["assigned_to"] == "u-rep"


async def test_manager_cannot_create_outside_team(committing_client, async_session_maker):
    """AC1: a manager handing a new customer outside their team gets the 403."""
    await seed_people(async_session_maker)
    resp = await _create(committing_client, BOSS, "u-other")
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "FORBIDDEN"
    assert await _contact_count(async_session_maker, "New Customer") == 0


async def test_admin_creates_for_anyone(committing_client, async_session_maker):
    """AC1: admins are unrestricted."""
    await seed_people(async_session_maker)
    resp = await _create(committing_client, ADMIN, "u-other")
    assert resp.status_code == 201
    assert resp.json()["data"]["assigned_to"] == "u-other"


# --- Import: assigned_to_email ---


async def _import(session_maker, user, rows) -> dict:
    async with session_maker() as session:
        result = await contact_service.import_contacts(session, rows, user)
        await session.commit()
    return result


async def _owner_of(session_maker, name: str):
    async with session_maker() as session:
        return (
            await session.execute(select(Contact.assigned_to).where(Contact.name == name))
        ).scalar_one_or_none()


async def test_import_rejects_out_of_reach_row_only(async_session_maker):
    """AC2: the out-of-reach row is skipped, the other rows still import."""
    await seed_people(async_session_maker)
    rows = [
        {"name": "Team Row", "assigned_to_email": "rep@example.com"},
        {"name": "Foreign Row", "assigned_to_email": "other@example.com"},
        {"name": "Blank Row"},
    ]
    result = await _import(async_session_maker, BOSS, rows)

    assert result["inserted"] == 2
    assert result["skipped"] == 1
    assert [e["row"] for e in result["errors"]] == [3]
    assert await _owner_of(async_session_maker, "Team Row") == "u-rep"
    assert await _contact_count(async_session_maker, "Foreign Row") == 0
    assert await _contact_count(async_session_maker, "Blank Row") == 1


async def test_import_refusal_reads_like_a_missing_account(async_session_maker):
    """AC2: same field, same message as "not found or inactive" -- existence not revealed."""
    await seed_people(async_session_maker)
    rows = [
        {"name": "Foreign Row", "assigned_to_email": "other@example.com"},
        {"name": "Ghost Row", "assigned_to_email": "nobody@example.com"},
    ]
    result = await _import(async_session_maker, REP, rows)

    foreign, ghost = result["errors"]
    del foreign["row"], ghost["row"]
    assert foreign == ghost
    assert foreign["field"] == "assigned_to_email"
    assert result["inserted"] == 0


async def test_import_within_reach_is_unchanged(async_session_maker):
    """AC3: a rep naming themselves, or an admin naming anyone, imports as before."""
    await seed_people(async_session_maker)
    rep_result = await _import(
        async_session_maker, REP, [{"name": "Rep Row", "assigned_to_email": "rep@example.com"}]
    )
    admin_result = await _import(
        async_session_maker,
        ADMIN,
        [{"name": "Admin Row", "assigned_to_email": "other@example.com"}],
    )

    assert rep_result["errors"] == admin_result["errors"] == []
    assert await _owner_of(async_session_maker, "Rep Row") == "u-rep"
    assert await _owner_of(async_session_maker, "Admin Row") == "u-other"


async def test_import_blank_owner_is_unchanged(async_session_maker):
    """AC3: no assigned_to_email -- a rep's row still falls back to the rep."""
    await seed_people(async_session_maker)
    result = await _import(async_session_maker, OTHER, [{"name": "Blank Row"}])
    assert result["errors"] == []
    assert await _owner_of(async_session_maker, "Blank Row") == "u-other"
