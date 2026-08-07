"""rename contacts.is_demo to is_gateway

Revision ID: 011
Revises: 010
Create Date: 2026-08-07

The whole crm_os/ai_chatbot deployments are themselves demo products, so a
per-contact "is this a demo" business classification doesn't mean anything
here. The only thing this column actually distinguishes is transport: did
the contact arrive through the shared WhatsApp demo gateway (whatsapp_gateway)
or through crm_os's own WhatsApp number. `is_gateway` names that precisely.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "011"
down_revision: Union[str, None] = "010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "contacts",
        "is_demo",
        new_column_name="is_gateway",
        existing_type=sa.Boolean(),
        existing_nullable=False,
        existing_server_default=sa.false(),
    )
    op.drop_index("idx_contacts_is_demo", table_name="contacts")
    op.create_index("idx_contacts_is_gateway", "contacts", ["is_gateway"])


def downgrade() -> None:
    op.alter_column(
        "contacts",
        "is_gateway",
        new_column_name="is_demo",
        existing_type=sa.Boolean(),
        existing_nullable=False,
        existing_server_default=sa.false(),
    )
    op.drop_index("idx_contacts_is_gateway", table_name="contacts")
    op.create_index("idx_contacts_is_demo", "contacts", ["is_demo"])
