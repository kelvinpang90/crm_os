"""add is_archived to contacts

Revision ID: 003
Revises: 002
Create Date: 2026-04-16
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "contacts",
        sa.Column("is_archived", sa.SmallInteger(), nullable=False, server_default="0"),
    )
    op.create_index("idx_is_archived", "contacts", ["is_archived"])


def downgrade() -> None:
    op.drop_index("idx_is_archived", table_name="contacts")
    op.drop_column("contacts", "is_archived")
