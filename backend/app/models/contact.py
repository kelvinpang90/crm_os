import uuid
from datetime import datetime, date
from decimal import Decimal

from sqlalchemy import (
    String, Enum, Text, DateTime, Date, Boolean, Index, JSON, DECIMAL,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Contact(Base):
    __tablename__ = "contacts"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    company: Mapped[str | None] = mapped_column(String(200), nullable=True)
    industry: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(
        Enum("潜在客户", "跟进中", "谈判中", "已成交", "已流失", name="contact_status"),
        nullable=False,
        default="潜在客户",
    )
    priority: Mapped[str] = mapped_column(
        Enum("高", "中", "低", name="contact_priority"),
        nullable=False,
        default="中",
    )
    deal_value: Mapped[Decimal] = mapped_column(
        DECIMAL(15, 2), nullable=False, default=Decimal("0.00")
    )
    email: Mapped[str | None] = mapped_column(String(200), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    assigned_to: Mapped[str | None] = mapped_column(String(36), nullable=True)
    last_contact: Mapped[date | None] = mapped_column(Date, nullable=True)
    tags: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    __table_args__ = (
        Index("idx_status", "status"),
        Index("idx_industry", "industry"),
        Index("idx_assigned_to", "assigned_to"),
        Index("idx_deleted_at", "deleted_at"),
    )
