"""Reassigning a contact has to carry its conversation history along.

`Message.assigned_to` is a copy of the contact's owner taken when the message is
stored, and the inbox filters on it. Left unsynced, handing a customer to a
colleague leaves the new owner with an empty inbox while the previous owner
still sees everything.
"""

from sqlalchemy import select

from app.models.contact import Contact
from app.models.message import Message
from app.models.user import User
from app.services import contact_service

_ADMIN = User(
    id="u-admin", name="Admin", email="admin@example.com",
    password_hash="x", role="admin",
)


def _message(msg_id: str, direction: str, owner: str) -> Message:
    return Message(
        id=msg_id, contact_id="c1", channel="whatsapp", direction=direction,
        sender_id="60111111111", recipient_id="crm", body="…", assigned_to=owner,
    )


async def test_reassign_transfers_message_history(async_session_maker):
    async with async_session_maker() as session:
        session.add_all([
            User(id="u-old", name="Old", email="old@example.com", password_hash="x", role="sales"),
            User(id="u-new", name="New", email="new@example.com", password_hash="x", role="sales"),
            Contact(id="c1", name="Acme Sdn Bhd", phone="60111111111", assigned_to="u-old"),
            _message("m1", "inbound", "u-old"),
            _message("m2", "outbound", "u-old"),
        ])
        await session.commit()

    async with async_session_maker() as session:
        await contact_service.update_contact(session, "c1", {"assigned_to": "u-new"}, _ADMIN)
        await session.commit()

    async with async_session_maker() as session:
        owners = (
            await session.execute(
                select(Message.assigned_to)
                .where(Message.contact_id == "c1")
                .order_by(Message.id)
            )
        ).scalars().all()

    assert owners == ["u-new", "u-new"]


async def test_unrelated_update_leaves_history_alone(async_session_maker):
    """Only a change of owner should touch messages — editing other fields must not."""
    async with async_session_maker() as session:
        session.add_all([
            User(id="u-old", name="Old", email="old@example.com", password_hash="x", role="sales"),
            Contact(id="c1", name="Acme Sdn Bhd", phone="60111111111", assigned_to="u-old"),
            _message("m1", "inbound", "u-old"),
        ])
        await session.commit()

    async with async_session_maker() as session:
        await contact_service.update_contact(session, "c1", {"company": "Acme Holdings"}, _ADMIN)
        await session.commit()

    async with async_session_maker() as session:
        owner = (
            await session.execute(select(Message.assigned_to).where(Message.id == "m1"))
        ).scalar_one()

    assert owner == "u-old"
