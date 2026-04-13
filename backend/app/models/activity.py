import uuid
from datetime import datetime

from sqlalchemy import String, Enum, Text, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Activity(Base):
    __tablename__ = "activities"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    contact_id: Mapped[str] = mapped_column(String(36), nullable=False)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False)
    type: Mapped[str] = mapped_column(
        Enum("电话", "邮件", "会面", "WhatsApp", "其他", "状态变更", name="activity_type"),
        nullable=False,
    )
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    follow_date: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )

    __table_args__ = (Index("idx_activity_contact_id", "contact_id"),)
