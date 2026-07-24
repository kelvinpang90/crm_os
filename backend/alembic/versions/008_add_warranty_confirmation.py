"""add warranty confirmation fields to projects (satisfaction score + signature)

Revision ID: 008
Revises: 007
Create Date: 2026-07-24

Adds 4 nullable columns to `projects` to record the customer satisfaction
score, feedback text, and hand-drawn signature captured when a project first
advances into step 12 (warranty_active). Existing projects already at step 12
are left as-is (nulls) per product decision: the gate only applies going
forward, no backfill.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

revision: str = "008"
down_revision: Union[str, None] = "007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("projects", sa.Column("satisfaction_score", sa.Integer(), nullable=True))
    op.add_column("projects", sa.Column("customer_feedback", sa.Text(), nullable=True))
    # base64 PNG data URI can exceed MySQL TEXT's 65KB cap; use LONGTEXT there.
    op.add_column(
        "projects",
        sa.Column("signature_data", sa.Text().with_variant(mysql.LONGTEXT(), "mysql"), nullable=True),
    )
    op.add_column("projects", sa.Column("signed_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("projects", "signed_at")
    op.drop_column("projects", "signature_data")
    op.drop_column("projects", "customer_feedback")
    op.drop_column("projects", "satisfaction_score")
