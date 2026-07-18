"""add project tracking tables + demo seed (self-contained module)

Revision ID: 007
Revises: 006
Create Date: 2026-07-18

Creates the two project tracking tables and seeds the demo projects in the same
migration, so `alembic upgrade head` (run by the deploy after `compose up`)
guarantees data is present. Demo data can later be refreshed via
POST /api/projects/seed-demo. Timestamps are relative to migration run time.
"""
import json
from datetime import datetime
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from app.data.project_seed import build_seed_rows

revision: str = "007"
down_revision: Union[str, None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "projects",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("customer_name", sa.String(200), nullable=False),
        sa.Column("address", sa.String(300), nullable=False, server_default=""),
        sa.Column("service_type", sa.String(100), nullable=False, server_default=""),
        sa.Column("project_manager", sa.String(100), nullable=False, server_default=""),
        sa.Column("current_step", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("idx_project_manager", "projects", ["project_manager"])
    op.create_index("idx_project_deleted_at", "projects", ["deleted_at"])

    op.create_table(
        "project_step_history",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("project_id", sa.String(36), nullable=False),
        sa.Column("step_no", sa.Integer(), nullable=False),
        sa.Column("entered_at", sa.DateTime(), nullable=False),
        sa.Column("updated_by", sa.String(100), nullable=False, server_default=""),
        sa.Column("note", sa.String(500), nullable=True),
        sa.Column("photos", sa.JSON(), nullable=True),
    )
    op.create_index("idx_step_project_id", "project_step_history", ["project_id"])

    # --- Seed demo data (relative to migration run time) ---
    project_rows, history_rows = build_seed_rows(datetime.utcnow())

    projects_tbl = sa.table(
        "projects",
        sa.column("id", sa.String),
        sa.column("customer_name", sa.String),
        sa.column("address", sa.String),
        sa.column("service_type", sa.String),
        sa.column("project_manager", sa.String),
        sa.column("current_step", sa.Integer),
        sa.column("deleted_at", sa.DateTime),
        sa.column("created_at", sa.DateTime),
        sa.column("updated_at", sa.DateTime),
    )
    op.bulk_insert(projects_tbl, project_rows)

    history_tbl = sa.table(
        "project_step_history",
        sa.column("id", sa.String),
        sa.column("project_id", sa.String),
        sa.column("step_no", sa.Integer),
        sa.column("entered_at", sa.DateTime),
        sa.column("updated_by", sa.String),
        sa.column("note", sa.String),
        sa.column("photos", sa.Text),  # JSON string; MySQL JSON column accepts it
    )
    op.bulk_insert(
        history_tbl,
        [{**r, "photos": json.dumps(r["photos"])} for r in history_rows],
    )


def downgrade() -> None:
    op.drop_index("idx_step_project_id", table_name="project_step_history")
    op.drop_table("project_step_history")
    op.drop_index("idx_project_deleted_at", table_name="projects")
    op.drop_index("idx_project_manager", table_name="projects")
    op.drop_table("projects")
