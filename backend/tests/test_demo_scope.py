"""Demo traffic from whatsapp_gateway must stay out of business views.

The CRM is itself a demo product, so what these tests protect is the curated
picture prospects are shown — seeded contacts and deals — from being diluted by
walk-in WhatsApp visitors (leads named after a phone number, worth RM 0).
"""

from sqlalchemy import select

from app.main import app
from app.dependencies import get_current_user
from app.routers import analytics
from app.models.contact import Contact
from app.models.deal import Deal
from app.models.message import Message
from app.models.user import User
from app.services import contact_service, dashboard_service, deal_service
from app.utils.demo_scope import message_not_demo

_ADMIN = User(
    id="u-admin", name="Admin", email="admin@example.com",
    password_hash="x", role="admin",
)


async def _seed_real_and_demo(session_maker) -> None:
    """One genuine lead and one gateway visitor, both created 'today'."""
    async with session_maker() as session:
        session.add_all([
            Contact(id="c-real", name="Genuine Sdn Bhd", phone="60111111111", is_gateway=False),
            Contact(id="c-demo", name="60122222222", phone="60122222222", is_gateway=True),
            Deal(id="d-real", contact_id="c-real", status="lead", priority="mid", amount=5000.0),
            Deal(id="d-demo", contact_id="c-demo", status="lead", priority="mid", amount=0.0),
        ])
        await session.commit()


async def test_admin_dashboard_excludes_demo(async_session_maker):
    await _seed_real_and_demo(async_session_maker)

    async with async_session_maker() as session:
        result = await dashboard_service.get_admin_dashboard(session)

    kpis = {k["key"]: k["value"] for k in result["kpis"]}
    assert kpis["new_leads_today"] == 1, "the gateway visitor must not count as a new lead"

    new_lead_stage = next(s for s in result["funnel"] if s["stage"] == "newLead")
    assert new_lead_stage["count"] == 1
    assert new_lead_stage["amount"] == 5000.0


async def test_analytics_deal_scope_excludes_demo(async_session_maker):
    """Exercises the analytics scope conditions rather than the endpoint: every
    deal query in that router is built from this list, but the endpoint itself
    can't run here because its trend query uses MySQL-only `date_format`."""
    await _seed_real_and_demo(async_session_maker)

    async with async_session_maker() as session:
        conditions = await analytics._get_scoped_deal_conditions(_ADMIN, session)
        deal_ids = (
            await session.execute(select(Deal.id).where(*conditions))
        ).scalars().all()

    assert deal_ids == ["d-real"]


async def test_contact_list_excludes_demo(async_session_maker):
    await _seed_real_and_demo(async_session_maker)

    async with async_session_maker() as session:
        result = await contact_service.list_contacts(session, _ADMIN)

    assert result["total"] == 1
    assert [c["id"] for c in result["data"]] == ["c-real"]


async def test_deal_list_excludes_demo(async_session_maker):
    await _seed_real_and_demo(async_session_maker)

    async with async_session_maker() as session:
        deals = await deal_service.list_deals(session, _ADMIN)

    assert [d["id"] for d in deals] == ["d-real"]


async def test_pipeline_excludes_demo(client, async_session_maker):
    await _seed_real_and_demo(async_session_maker)

    app.dependency_overrides[get_current_user] = lambda: _ADMIN
    try:
        resp = await client.get("/api/pipeline")
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert resp.status_code == 200
    lead_stage = next(s for s in resp.json()["data"]["stages"] if s["status"] == "lead")
    assert lead_stage["count"] == 1
    assert [d["id"] for d in lead_stage["deals"]] == ["d-real"]


async def test_demo_contact_still_reachable_by_id(async_session_maker):
    """The carve-out: demo rows stay openable so an operator can work the
    conversation the inbox handed them."""
    await _seed_real_and_demo(async_session_maker)

    async with async_session_maker() as session:
        contact = await contact_service.get_contact(session, "c-demo")

    assert contact is not None
    assert contact["id"] == "c-demo"


async def test_message_predicate_keeps_contactless_messages(async_session_maker):
    """`Message.contact_id` is nullable, and `NULL NOT IN (...)` is NULL — a naive
    predicate would silently drop every message with no contact attached."""
    async with async_session_maker() as session:
        session.add_all([
            Contact(id="c-demo", name="60122222222", phone="60122222222", is_gateway=True),
            Message(
                id="m-demo", contact_id="c-demo", channel="whatsapp", direction="inbound",
                sender_id="60122222222", recipient_id="crm", body="hi",
            ),
            Message(
                id="m-orphan", contact_id=None, channel="email", direction="inbound",
                sender_id="someone@example.com", recipient_id="crm", body="unmatched",
            ),
        ])
        await session.commit()

        kept = (
            await session.execute(select(Message.id).where(message_not_demo()))
        ).scalars().all()

    assert kept == ["m-orphan"]
