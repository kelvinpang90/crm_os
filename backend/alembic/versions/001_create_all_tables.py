"""create all tables

Revision ID: 001
Revises:
Create Date: 2026-04-12
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Users
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("email", sa.String(200), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column(
            "role",
            sa.Enum("admin", "manager", "sales", name="user_role"),
            nullable=False,
            server_default="sales",
        ),
        sa.Column("avatar_url", sa.Text, nullable=True),
        sa.Column(
            "language",
            sa.Enum("zh", "en", name="user_language"),
            nullable=False,
            server_default="zh",
        ),
        sa.Column("manager_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("1")),
        sa.Column(
            "created_at", sa.DateTime, nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at",
            sa.DateTime,
            nullable=False,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )

    # Contacts
    op.create_table(
        "contacts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("company", sa.String(200), nullable=True),
        sa.Column("industry", sa.String(50), nullable=True),
        sa.Column(
            "status",
            sa.Enum("潜在客户", "跟进中", "谈判中", "已成交", "已流失", name="contact_status"),
            nullable=False,
            server_default="潜在客户",
        ),
        sa.Column(
            "priority",
            sa.Enum("高", "中", "低", name="contact_priority"),
            nullable=False,
            server_default="中",
        ),
        sa.Column(
            "deal_value", sa.DECIMAL(15, 2), nullable=False, server_default="0.00"
        ),
        sa.Column("email", sa.String(200), nullable=True),
        sa.Column("phone", sa.String(30), nullable=True),
        sa.Column("address", sa.Text, nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("assigned_to", sa.String(36), nullable=True),
        sa.Column("last_contact", sa.Date, nullable=True),
        sa.Column("tags", sa.JSON, nullable=True),
        sa.Column("deleted_at", sa.DateTime, nullable=True),
        sa.Column(
            "created_at", sa.DateTime, nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at",
            sa.DateTime,
            nullable=False,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )
    op.create_index("idx_status", "contacts", ["status"])
    op.create_index("idx_industry", "contacts", ["industry"])
    op.create_index("idx_assigned_to", "contacts", ["assigned_to"])
    op.create_index("idx_deleted_at", "contacts", ["deleted_at"])

    # Activities
    op.create_table(
        "activities",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("contact_id", sa.String(36), nullable=False),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column(
            "type",
            sa.Enum("电话", "邮件", "会面", "WhatsApp", "其他", "状态变更", name="activity_type"),
            nullable=False,
        ),
        sa.Column("content", sa.Text, nullable=True),
        sa.Column(
            "follow_date", sa.DateTime, nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "created_at", sa.DateTime, nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_index("idx_activity_contact_id", "activities", ["contact_id"])

    # Tasks
    op.create_table(
        "tasks",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("contact_id", sa.String(36), nullable=True),
        sa.Column("assigned_to", sa.String(36), nullable=True),
        sa.Column(
            "priority",
            sa.Enum("高", "中", "低", name="task_priority"),
            nullable=False,
            server_default="中",
        ),
        sa.Column("due_date", sa.Date, nullable=True),
        sa.Column("is_done", sa.Boolean, nullable=False, server_default=sa.text("0")),
        sa.Column("done_at", sa.DateTime, nullable=True),
        sa.Column(
            "created_at", sa.DateTime, nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at",
            sa.DateTime,
            nullable=False,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )
    op.create_index("idx_task_assigned_to", "tasks", ["assigned_to"])
    op.create_index("idx_task_due_date", "tasks", ["due_date"])
    op.create_index("idx_task_is_done", "tasks", ["is_done"])

    # Settings
    op.create_table(
        "settings",
        sa.Column("key", sa.String(100), primary_key=True),
        sa.Column("value", sa.JSON, nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime,
            nullable=False,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )

    # Messages
    op.create_table(
        "messages",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("contact_id", sa.String(36), nullable=True),
        sa.Column(
            "channel",
            sa.Enum("whatsapp", "email", name="message_channel"),
            nullable=False,
        ),
        sa.Column(
            "direction",
            sa.Enum("inbound", "outbound", name="message_direction"),
            nullable=False,
        ),
        sa.Column("sender_id", sa.String(200), nullable=False),
        sa.Column("recipient_id", sa.String(200), nullable=False),
        sa.Column("subject", sa.String(500), nullable=True),
        sa.Column("body", sa.Text, nullable=False),
        sa.Column("external_id", sa.String(200), unique=True, nullable=True),
        sa.Column("is_read", sa.Boolean, nullable=False, server_default=sa.text("0")),
        sa.Column("assigned_to", sa.String(36), nullable=True),
        sa.Column(
            "created_at", sa.DateTime, nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_index("idx_msg_contact_id", "messages", ["contact_id"])
    op.create_index("idx_msg_channel", "messages", ["channel"])
    op.create_index("idx_msg_sender_id", "messages", ["sender_id"])
    op.create_index("idx_msg_created_at", "messages", ["created_at"])

    # Routing Rules
    op.create_table(
        "routing_rules",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("1")),
        sa.Column("priority", sa.Integer, nullable=False, server_default="0"),
        sa.Column(
            "strategy",
            sa.Enum("workload", "region", "win_rate", name="routing_strategy"),
            nullable=False,
        ),
        sa.Column("conditions", sa.JSON, nullable=True),
        sa.Column("target_users", sa.JSON, nullable=True),
        sa.Column("created_by", sa.String(36), nullable=True),
        sa.Column(
            "created_at", sa.DateTime, nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at",
            sa.DateTime,
            nullable=False,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )

    # Sales Targets
    op.create_table(
        "sales_targets",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("year", sa.SmallInteger, nullable=False),
        sa.Column("month", sa.SmallInteger, nullable=False),
        sa.Column(
            "target_amount", sa.DECIMAL(15, 2), nullable=False, server_default="0.00"
        ),
        sa.Column("target_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column(
            "created_at", sa.DateTime, nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at",
            sa.DateTime,
            nullable=False,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
        sa.UniqueConstraint("user_id", "year", "month", name="uk_user_year_month"),
    )


def downgrade() -> None:
    op.drop_table("sales_targets")
    op.drop_table("routing_rules")
    op.drop_table("messages")
    op.drop_table("settings")
    op.drop_table("tasks")
    op.drop_table("activities")
    op.drop_table("contacts")
    op.drop_table("users")
