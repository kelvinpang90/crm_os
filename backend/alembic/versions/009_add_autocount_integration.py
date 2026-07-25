"""add AutoCount Cloud Accounting sync tables + contact mapping field

Revision ID: 009
Revises: 008
Create Date: 2026-07-24

Adds:
- `contacts.autocount_customer_code` — external key (AutoCount Debtor.accNo).
  Contacts are upserted directly from the AutoCount debtor listing during sync
  (see autocount_service._sync_customers) keyed on this column — CRM contacts
  are not created manually in this workflow, so no fuzzy-matching/dedup is needed.
- `autocount_documents` — synced snapshot of AutoCount invoice/quotation listings,
  linked to `contacts` via `contact_id` (nullable if a document's debtorCode
  doesn't match any known contact, e.g. a stale/inactive AutoCount customer).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "009"
down_revision: Union[str, None] = "008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("contacts", sa.Column("autocount_customer_code", sa.String(12), nullable=True))
    op.create_index("idx_autocount_customer_code", "contacts", ["autocount_customer_code"])

    op.create_table(
        "autocount_documents",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("doc_type", sa.Enum("invoice", "quotation", name="autocount_doc_type"), nullable=False),
        sa.Column("doc_no", sa.String(50), nullable=False),
        sa.Column("customer_code", sa.String(12), nullable=False),
        sa.Column("contact_id", sa.String(36), nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default=""),
        sa.Column("total_amount", sa.DECIMAL(15, 2), nullable=False, server_default="0.00"),
        sa.Column("currency_code", sa.String(10), nullable=False, server_default=""),
        sa.Column("doc_date", sa.Date(), nullable=True),
        sa.Column("outstanding_amount", sa.DECIMAL(15, 2), nullable=True),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("validity", sa.String(100), nullable=True),
        sa.Column("line_items", sa.JSON(), nullable=True),
        sa.Column("synced_at", sa.DateTime(), nullable=False),
    )
    op.create_index(
        "idx_autocount_doc_type_no", "autocount_documents", ["doc_type", "doc_no"], unique=True
    )
    op.create_index("idx_autocount_doc_contact_id", "autocount_documents", ["contact_id"])
    op.create_index("idx_autocount_doc_customer_code", "autocount_documents", ["customer_code"])


def downgrade() -> None:
    op.drop_index("idx_autocount_doc_customer_code", table_name="autocount_documents")
    op.drop_index("idx_autocount_doc_contact_id", table_name="autocount_documents")
    op.drop_index("idx_autocount_doc_type_no", table_name="autocount_documents")
    op.drop_table("autocount_documents")

    op.drop_index("idx_autocount_customer_code", table_name="contacts")
    op.drop_column("contacts", "autocount_customer_code")
