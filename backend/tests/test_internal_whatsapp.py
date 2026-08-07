import pytest
from sqlalchemy import select

from app.config import settings
from app.models.contact import Contact
from app.models.deal import Deal
from app.models.message import Message


@pytest.fixture(autouse=True)
def _internal_secret(monkeypatch):
    monkeypatch.setattr(settings, "internal_shared_secret", "test-secret")


async def test_missing_secret_rejected(client):
    resp = await client.post("/internal/whatsapp/inbound", json={"message": {}})
    assert resp.status_code == 403


async def test_wrong_secret_rejected(client):
    resp = await client.post(
        "/internal/whatsapp/inbound",
        json={"message": {}},
        headers={"X-Internal-Secret": "nope"},
    )
    assert resp.status_code == 403


async def test_valid_message_creates_demo_contact(client, async_session_maker):
    payload = {
        "message": {
            "from": "60123456789",
            "id": "wamid.ABC123",
            "type": "text",
            "text": {"body": "hi"},
        }
    }
    resp = await client.post(
        "/internal/whatsapp/inbound",
        json=payload,
        headers={"X-Internal-Secret": "test-secret"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["messages"]) == 1
    assert body["messages"][0]["to"] == "60123456789"
    assert "已收到" in body["messages"][0]["text"]["body"]

    async with async_session_maker() as session:
        contact = (
            await session.execute(select(Contact).where(Contact.phone == "60123456789"))
        ).scalar_one()
        assert contact.is_gateway is True

        deal = (
            await session.execute(select(Deal).where(Deal.contact_id == contact.id))
        ).scalar_one()
        assert deal.status == "lead"

        message = (
            await session.execute(select(Message).where(Message.external_id == "wamid.ABC123"))
        ).scalar_one()
        assert message.direction == "inbound"
        assert message.body == "hi"


async def test_duplicate_message_no_confirmation(client):
    payload = {
        "message": {
            "from": "60111111111",
            "id": "wamid.DUP1",
            "type": "text",
            "text": {"body": "hello"},
        }
    }
    headers = {"X-Internal-Secret": "test-secret"}

    first = await client.post("/internal/whatsapp/inbound", json=payload, headers=headers)
    assert first.status_code == 200
    assert len(first.json()["messages"]) == 1

    second = await client.post("/internal/whatsapp/inbound", json=payload, headers=headers)
    assert second.status_code == 200
    assert second.json()["messages"] == []
