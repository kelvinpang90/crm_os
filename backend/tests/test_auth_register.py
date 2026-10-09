"""Accounts are created by an admin, not by whoever finds the login page.

A self-registered account came out as an active `sales` user, and the routing
engine hands new leads to the least-loaded active rep -- which a brand-new
account with no customers always is. Closing the door is the whole fix.
"""

from sqlalchemy import func, select

from app.models.user import User


async def test_public_registration_is_closed(client, async_session_maker):
    resp = await client.post(
        "/api/auth/register",
        json={
            "name": "Stranger",
            "email": "stranger@example.com",
            "password": "Passw0rd1",
            "confirm_password": "Passw0rd1",
        },
    )

    assert resp.status_code in (404, 405)
    assert "access_token" not in resp.text
    async with async_session_maker() as session:
        count = (await session.execute(select(func.count()).select_from(User))).scalar()
    assert count == 0
