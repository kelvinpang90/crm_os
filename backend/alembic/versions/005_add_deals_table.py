"""add deals table and deal_id to activities

Revision ID: 005
Revises: 004
Create Date: 2026-04-17
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create deals table
    op.create_table(
        "deals",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("contact_id", sa.String(36), nullable=False),
        sa.Column("title", sa.String(200), nullable=True),
        sa.Column(
            "status",
            sa.Enum("lead", "following", "negotiating", "won", "lost", name="deal_status"),
            nullable=False,
            server_default="lead",
        ),
        sa.Column(
            "priority",
            sa.Enum("high", "mid", "low", name="deal_priority"),
            nullable=False,
            server_default="mid",
        ),
        sa.Column("amount", sa.DECIMAL(15, 2), nullable=False, server_default="0.00"),
        sa.Column("assigned_to", sa.String(36), nullable=True),
        sa.Column("won_at", sa.DateTime(), nullable=True),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("idx_deal_contact_id", "deals", ["contact_id"])
    op.create_index("idx_deal_status", "deals", ["status"])
    op.create_index("idx_deal_assigned_to", "deals", ["assigned_to"])
    op.create_index("idx_deal_won_at", "deals", ["won_at"])
    op.create_index("idx_deal_deleted_at", "deals", ["deleted_at"])

    # 2. Migrate existing contacts → deals (one deal per contact)
    op.execute("""
        INSERT INTO deals (id, contact_id, title, status, priority, amount,
                           assigned_to, won_at, created_at, updated_at)
        SELECT
            UUID(),
            id,
            NULL,
            status,
            priority,
            deal_value,
            assigned_to,
            won_at,
            created_at,
            NOW()
        FROM contacts
        WHERE deleted_at IS NULL
    """)

    # 3. Back-fill won_at for historical won deals that have no won_at
    op.execute("""
        UPDATE deals SET won_at = updated_at
        WHERE status = 'won' AND won_at IS NULL
    """)

    # 4. Drop deal-related columns from contacts
    op.drop_index("idx_is_archived", table_name="contacts")  # recreate after drops
    op.drop_index("idx_won_at", table_name="contacts")
    op.drop_column("contacts", "won_at")
    op.drop_column("contacts", "status")
    op.drop_column("contacts", "deal_value")
    op.drop_column("contacts", "priority")
    op.create_index("idx_is_archived", "contacts", ["is_archived"])

    # 5. Add deal_id to activities
    op.add_column("activities", sa.Column("deal_id", sa.String(36), nullable=True))
    op.create_index("idx_activity_deal_id", "activities", ["deal_id"])


def downgrade() -> None:
    # Reverse: restore columns to contacts, drop deals table
    op.drop_index("idx_activity_deal_id", table_name="activities")
    op.drop_column("activities", "deal_id")

    op.drop_index("idx_is_archived", table_name="contacts")
    op.add_column("contacts", sa.Column("priority", sa.Enum("high", "mid", "low", name="contact_priority"), nullable=True))
    op.add_column("contacts", sa.Column("deal_value", sa.DECIMAL(15, 2), nullable=True))
    op.add_column("contacts", sa.Column("status", sa.Enum("lead", "following", "negotiating", "won", "lost", name="contact_status"), nullable=True))
    op.add_column("contacts", sa.Column("won_at", sa.DateTime(), nullable=True))
    op.create_index("idx_is_archived", "contacts", ["is_archived"])
    op.create_index("idx_won_at", "contacts", ["won_at"])

    op.drop_index("idx_deal_deleted_at", table_name="deals")
    op.drop_index("idx_deal_won_at", table_name="deals")
    op.drop_index("idx_deal_assigned_to", table_name="deals")
    op.drop_index("idx_deal_status", table_name="deals")
    op.drop_index("idx_deal_contact_id", table_name="deals")
    op.drop_table("deals")
