"""make deal_id required in activities

Revision ID: 006
Revises: 005
Create Date: 2026-04-18
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Fill NULL deal_id with the contact's earliest non-deleted deal
    op.execute("""
        UPDATE activities
        SET deal_id = (
            SELECT id FROM deals
            WHERE deals.contact_id = activities.contact_id
              AND deals.deleted_at IS NULL
            ORDER BY deals.created_at ASC
            LIMIT 1
        )
        WHERE deal_id IS NULL
    """)

    # Delete any remaining orphaned activities (contact has no deal at all)
    op.execute("DELETE FROM activities WHERE deal_id IS NULL")

    op.alter_column("activities", "deal_id", existing_type=sa.String(36), nullable=False)


def downgrade() -> None:
    op.alter_column("activities", "deal_id", existing_type=sa.String(36), nullable=True)
