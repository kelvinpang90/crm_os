"""update enums to english

Revision ID: 002
Revises: 001
Create Date: 2026-04-14
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE contacts MODIFY COLUMN status "
        "ENUM('lead','following','negotiating','won','lost') NOT NULL DEFAULT 'lead'"
    )
    op.execute(
        "ALTER TABLE contacts MODIFY COLUMN priority "
        "ENUM('high','mid','low') NOT NULL DEFAULT 'mid'"
    )
    op.execute(
        "ALTER TABLE activities MODIFY COLUMN type "
        "ENUM('phone','email','meeting','WhatsApp','other','status change') NOT NULL"
    )
    op.execute(
        "ALTER TABLE tasks MODIFY COLUMN priority "
        "ENUM('high','mid','low') NOT NULL DEFAULT 'mid'"
    )


def downgrade() -> None:
    op.execute(
        "ALTER TABLE contacts MODIFY COLUMN status "
        "ENUM('潜在客户','跟进中','谈判中','已成交','已流失') NOT NULL DEFAULT '潜在客户'"
    )
    op.execute(
        "ALTER TABLE contacts MODIFY COLUMN priority "
        "ENUM('高','中','低') NOT NULL DEFAULT '中'"
    )
    op.execute(
        "ALTER TABLE activities MODIFY COLUMN type "
        "ENUM('电话','邮件','会面','WhatsApp','其他','状态变更') NOT NULL"
    )
    op.execute(
        "ALTER TABLE tasks MODIFY COLUMN priority "
        "ENUM('高','中','低') NOT NULL DEFAULT '中'"
    )
