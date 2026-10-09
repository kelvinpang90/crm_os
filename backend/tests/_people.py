"""The cast shared by the access tests.

REP reports to BOSS; OTHER is a rep on nobody's team. Each owns one customer,
and one customer belongs to nobody. Detached `User` objects stand in for the
logged-in user; the rows written by `seed_people` back the team lookups.
"""
from contextlib import contextmanager

from app.dependencies import get_current_user
from app.main import app
from app.models.contact import Contact
from app.models.user import User

REP = User(id="u-rep", name="Rep", email="rep@example.com", password_hash="x",
           role="sales", manager_id="u-boss")
OTHER = User(id="u-other", name="Other", email="other@example.com", password_hash="x",
             role="sales")
BOSS = User(id="u-boss", name="Boss", email="boss@example.com", password_hash="x",
            role="manager")
ADMIN = User(id="u-admin", name="Admin", email="admin@example.com", password_hash="x",
             role="admin")


async def seed_people(session_maker) -> None:
    async with session_maker() as session:
        session.add_all([
            User(id="u-rep", name="Rep", email="rep@example.com", password_hash="x",
                 role="sales", manager_id="u-boss"),
            User(id="u-other", name="Other", email="other@example.com", password_hash="x",
                 role="sales"),
            User(id="u-boss", name="Boss", email="boss@example.com", password_hash="x",
                 role="manager"),
            User(id="u-admin", name="Admin", email="admin@example.com", password_hash="x",
                 role="admin"),
            Contact(id="c-mine", name="Mine", phone="60111111111", assigned_to="u-rep"),
            Contact(id="c-theirs", name="Theirs", phone="60122222222", assigned_to="u-other"),
            Contact(id="c-orphan", name="Orphan", phone="60133333333", assigned_to=None),
        ])
        await session.commit()


@contextmanager
def logged_in_as(user: User):
    app.dependency_overrides[get_current_user] = lambda: user
    try:
        yield
    finally:
        app.dependency_overrides.pop(get_current_user, None)
