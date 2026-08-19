"""Bulk import can hand ownerless rows to a sales rep.

Import is the one entry point that never consulted the routing engine, so an
admin importing a sheet with no owner column left every contact ownerless —
invisible to sales and managers in both the contact list and the inbox.
"""

import pytest
from sqlalchemy import select

from app.models.contact import Contact
from app.models.deal import Deal
from app.models.user import User
from app.services import contact_service

ADMIN = User(id="u-admin", name="Admin", email="admin@example.com",
             password_hash="x", role="admin")

ROWS = [{"name": "Acme Sdn Bhd", "company": "Acme", "email": "hi@acme.com"}]


async def _seed_reps(session_maker) -> None:
    async with session_maker() as session:
        session.add_all([
            User(id="u-rep1", name="Rep One", email="r1@example.com",
                 password_hash="x", role="sales"),
            User(id="u-rep2", name="Rep Two", email="r2@example.com",
                 password_hash="x", role="sales"),
        ])
        await session.commit()


async def _import(session_maker, **kwargs) -> Contact:
    async with session_maker() as session:
        await contact_service.import_contacts(session, ROWS, ADMIN, **kwargs)
        await session.commit()
    async with session_maker() as session:
        return (
            await session.execute(select(Contact).where(Contact.name == "Acme Sdn Bhd"))
        ).scalar_one()


async def test_without_auto_assign_contact_stays_ownerless(async_session_maker):
    """Existing behaviour is the default — the option has to be asked for."""
    await _seed_reps(async_session_maker)
    contact = await _import(async_session_maker)
    assert contact.assigned_to is None


@pytest.mark.parametrize("strategy", ["rules", "workload", "win_rate"])
async def test_auto_assign_gives_the_contact_an_owner(async_session_maker, strategy):
    await _seed_reps(async_session_maker)
    contact = await _import(async_session_maker, auto_assign=True, assign_strategy=strategy)
    assert contact.assigned_to in {"u-rep1", "u-rep2"}


async def test_assign_to_me_uses_the_importer(async_session_maker):
    await _seed_reps(async_session_maker)
    contact = await _import(async_session_maker, auto_assign=True, assign_strategy="me")
    assert contact.assigned_to == "u-admin"


async def test_deal_inherits_the_resolved_owner(async_session_maker):
    """The deal is built after the contact and must not keep the pre-routing value."""
    await _seed_reps(async_session_maker)
    contact = await _import(async_session_maker, auto_assign=True, assign_strategy="workload")

    async with async_session_maker() as session:
        deal = (
            await session.execute(select(Deal).where(Deal.contact_id == contact.id))
        ).scalar_one()

    assert deal.assigned_to == contact.assigned_to
    assert deal.assigned_to is not None


async def test_explicit_owner_in_the_sheet_wins(async_session_maker):
    """auto_assign is a fallback, not an override."""
    await _seed_reps(async_session_maker)
    rows = [{"name": "Acme Sdn Bhd", "assigned_to_email": "r2@example.com"}]

    async with async_session_maker() as session:
        await contact_service.import_contacts(
            session, rows, ADMIN, auto_assign=True, assign_strategy="me"
        )
        await session.commit()

    async with async_session_maker() as session:
        contact = (
            await session.execute(select(Contact).where(Contact.name == "Acme Sdn Bhd"))
        ).scalar_one()

    assert contact.assigned_to == "u-rep2"


async def test_no_sales_reps_leaves_it_ownerless_without_erroring(async_session_maker):
    contact = await _import(async_session_maker, auto_assign=True, assign_strategy="workload")
    assert contact.assigned_to is None
