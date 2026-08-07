"""add is_demo flag to contacts

Revision ID: 010
Revises: 009
Create Date: 2026-08-07

Marks contacts that originated from the shared WhatsApp demo gateway
(whatsapp_gateway -> POST /internal/whatsapp/inbound), as opposed to the
project's own real WhatsApp number. `send_message()` uses this to decide
whether an admin's manual reply should go through the gateway's outbound
endpoint or straight to the Graph API.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "010"
down_revision: Union[str, None] = "009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "contacts",
        sa.Column("is_demo", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_index("idx_contacts_is_demo", "contacts", ["is_demo"])


def downgrade() -> None:
    op.drop_index("idx_contacts_is_demo", table_name="contacts")
    op.drop_column("contacts", "is_demo")
