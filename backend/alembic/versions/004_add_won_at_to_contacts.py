"""add won_at to contacts

Revision ID: 004
Revises: 003
Create Date: 2026-04-17
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "contacts",
        sa.Column("won_at", sa.DateTime(), nullable=True),
    )
    op.create_index("idx_won_at", "contacts", ["won_at"])


def downgrade() -> None:
    op.drop_index("idx_won_at", table_name="contacts")
    op.drop_column("contacts", "won_at")
